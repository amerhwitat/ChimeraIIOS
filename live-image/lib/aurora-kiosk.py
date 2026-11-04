#!/usr/bin/env python3
"""Aurora WebKit kiosk with a local-file-only, allow-listed native IPC bridge."""
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, Gtk, GLib, WebKit2  # noqa: E402

DEFAULT_URI = "file:///opt/aurora/desktop/aurora-shell/index.html"
TRUSTED_URIS = {"file:///opt/aurora/desktop/aurora-shell/index.html", "file:///opt/aurora/desktop/index.html"}
REGISTRY_SOCKET = "/run/chimera/registry.sock"
SMB_TOOL = "/usr/lib/chimera/network/smb-browse.py"
DIRECTORY_TOOL = "/usr/lib/chimera/network/directoryctl.py"
IMAGE_TOOL = "/usr/lib/chimera/storage/mount-image.py"

BRIDGE_JS = r"""
(() => {
  const pending = new Map(); let sequence = 0;
  const call = (service, method, args = {}) => new Promise((resolve, reject) => {
    const id = String(++sequence);
    pending.set(id, {resolve, reject});
    window.webkit.messageHandlers.chimera.postMessage(JSON.stringify({id, service, method, args}));
  });
  window.__chimeraResolve = (id, ok, value) => {
    const item = pending.get(String(id)); if (!item) return;
    pending.delete(String(id));
    ok ? item.resolve(value) : item.reject(new Error(value && value.message || "Native operation failed"));
  };
  window.chimeraRegistry = {
    list: () => call("registry", "list"),
    read: hive => call("registry", "read", {hive}),
    set: value => call("registry", "set", value),
    delete: value => call("registry", "delete", value)
  };
  window.chimeraNetwork = {
    browseSmb: host => call("network", "browseSmb", {host}),
    openSmb: (host, share) => call("network", "openSmb", {host, share}),
    discoverSmb: () => call("network", "discoverSmb"),
    joinDomain: (domain, user) => call("network", "joinDomain", {domain, user}),
    realmStatus: () => call("network", "realmStatus"),
    ldapSearch: (uri, base, filter) => call("network", "ldapSearch", {uri, base, filter})
  };
  window.chimeraStorage = {
    selectIso: () => call("storage", "selectIso"),
    mountIso: path => call("storage", "mountIso", {path}),
    mountOpticalDrive: device => call("storage", "mountOpticalDrive", {device}),
    unmountIso: device => call("storage", "unmountIso", {device})
  };
})();
"""

def display_geometry():
    display = Gdk.Display.get_default()
    if display is not None:
        monitor = display.get_primary_monitor()
        if monitor is not None:
            geometry = monitor.get_geometry()
            if geometry.width > 0 and geometry.height > 0:
                return geometry.x, geometry.y, geometry.width, geometry.height
    screen = Gdk.Screen.get_default()
    if screen is not None:
        return 0, 0, screen.get_width(), screen.get_height()
    return 0, 0, 1024, 768

def registry_call(request):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect(REGISTRY_SOCKET)
        sock.sendall((json.dumps(request, separators=(",", ":")) + "\n").encode())
        stream = sock.makefile("rb")
        response = json.loads(stream.readline(2 << 20))
    if not response.get("ok"):
        raise RuntimeError(response.get("message", response.get("error", "registry request failed")))
    return response

def command_json(argv, timeout=60):
    env = os.environ.copy()
    env.update({"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                            check=False, env=env)
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout[-12000:], "stderr": result.stderr[-3000:]}
    if result.returncode:
        raise RuntimeError(payload.get("error") or payload.get("stderr") or result.stderr[-2000:] or "operation failed")
    return payload

def choose_iso(parent):
    dialog = Gtk.FileChooserDialog(
        title="Choose an ISO image", parent=parent, action=Gtk.FileChooserAction.OPEN,
        buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
    filt = Gtk.FileFilter()
    filt.set_name("Optical images (*.iso)")
    filt.add_pattern("*.iso")
    filt.add_pattern("*.ISO")
    dialog.add_filter(filt)
    response = dialog.run()
    filename = dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
    dialog.destroy()
    return filename

def dispatch(service, method, args, parent):
    if service == "registry":
        if method == "list":
            return registry_call({"op": "list"})
        if method == "read":
            return registry_call({"op": "read", "hive": args.get("hive")})
        if method == "set":
            return registry_call({"op": "set", "hive": args.get("hive"), "path": args.get("path"), "type": args.get("type"), "value": args.get("value"), "generation": args.get("generation")})
        if method == "delete":
            return registry_call({"op": "delete", "hive": args.get("hive"), "path": args.get("path"), "generation": args.get("generation")})
    if service == "network":
        if method == "browseSmb":
            host = args.get("host", "")
            return command_json([sys.executable, SMB_TOOL, host], timeout=30)
        if method == "discoverSmb":
            return command_json([sys.executable, SMB_TOOL, "--network"], timeout=40)
        if method == "openSmb":
            host = args.get("host", "")
            share = args.get("share", "")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]{0,252}", host):
                raise ValueError("invalid SMB host")
            if share not in (None, "") and (not isinstance(share, str) or
                    not re.fullmatch(r"[A-Za-z0-9._$ -]{1,80}", share) or share in (".", "..")):
                raise ValueError("invalid SMB share name")
            if not shutil.which("gio"):
                raise RuntimeError("GVFS/GIO is required to open SMB shares")
            from urllib.parse import quote
            uri = "smb://" + host + (("/" + quote(share, safe="")) if share else "/")
            result = subprocess.run(["gio", "open", uri], capture_output=True, text=True,
                                    timeout=30, check=False,
                                    env={**os.environ, "PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"})
            if result.returncode:
                raise RuntimeError(result.stderr[-2000:] or "GVFS could not open SMB share")
            return {"opened": uri}
        if method == "joinDomain":
            argv = [sys.executable, DIRECTORY_TOOL, "join", args.get("domain", ""), "--elevate"]
            if args.get("user"):
                argv += ["--user", args["user"]]
            return command_json(argv, timeout=180)
        if method == "realmStatus":
            return command_json([sys.executable, DIRECTORY_TOOL, "status"], timeout=20)
        if method == "ldapSearch":
            return command_json([sys.executable, DIRECTORY_TOOL, "ldap-search",
                                 args.get("uri", ""), args.get("base", ""),
                                 args.get("filter", "")], timeout=60)
    if service == "storage":
        if method == "selectIso":
            return choose_iso(parent)
        if method == "mountIso":
            return command_json([sys.executable, IMAGE_TOOL, "mount", args.get("path", "")], timeout=90)
        if method == "mountOpticalDrive":
            return command_json([sys.executable, IMAGE_TOOL, "mount-device", args.get("device", "/dev/sr0")], timeout=90)
        if method == "unmountIso":
            return command_json([sys.executable, IMAGE_TOOL, "unmount", args.get("device", "")], timeout=60)
    raise ValueError("unsupported native bridge operation")

def main():
    uri = os.environ.get("AURORA_DESKTOP_URI") or (
        sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI
    )
    x, y, width, height = display_geometry()
    print(f"[Aurora] display={width}x{height} origin={x},{y}; opening {uri}", flush=True)

    win = Gtk.Window()
    win.set_title("Aurora Desktop")
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_keep_above(False)
    win.set_default_size(width, height)
    win.set_position(Gtk.WindowPosition.CENTER)

    trusted_local_shell = uri.split("?", 1)[0].split("#", 1)[0] in TRUSTED_URIS
    manager = WebKit2.UserContentManager()
    manager.register_script_message_handler("chimera")
    if trusted_local_shell:
        script = WebKit2.UserScript.new(
            BRIDGE_JS, WebKit2.UserContentInjectedFrames.TOP_FRAME,
            WebKit2.UserScriptInjectionTime.START, None, None)
        manager.add_script(script)
    view = WebKit2.WebView.new_with_user_content_manager(manager)
    view.set_hexpand(True)
    view.set_vexpand(True)
    try:
        settings = view.get_settings()
        settings.set_property("allow-file-access-from-file-urls", True)
        settings.set_property("allow-universal-access-from-file-urls", True)
        settings.set_property("enable-write-console-messages-to-stdout", True)
        settings.set_property("hardware-acceleration-policy", WebKit2.HardwareAccelerationPolicy.NEVER)
        settings.set_property("enable-smooth-scrolling", True)
        settings.set_property("enable-accelerated-2d-canvas", False)
        settings.set_property("enable-webgl", False)
    except Exception as exc:
        print("[Aurora] WebKit settings warning:", exc, flush=True)

    if trusted_local_shell:
        def reply(message_id, ok, value):
            encoded = json.dumps(value, separators=(",", ":"))
            script = "window.__chimeraResolve(" + json.dumps(message_id) + "," + ("true" if ok else "false") + "," + encoded + ");"
            view.run_javascript(script, None, None, None)
            return GLib.SOURCE_REMOVE

        def on_message(_manager, message):
            try:
                request = json.loads(message.get_js_value().to_string())
                message_id = str(request.get("id", ""))
                service = request.get("service")
                method = request.get("method")
                args = request.get("args") or {}
                if not message_id or len(message_id) > 32 or not isinstance(args, dict):
                    raise ValueError("invalid bridge request")
                if service == "storage" and method == "selectIso":
                    try:
                        value = dispatch(service, method, args, win)
                        GLib.idle_add(reply, message_id, True, value)
                    except Exception as exc:
                        GLib.idle_add(reply, message_id, False, {"message": str(exc)})
                    return
                def worker():
                    try:
                        value = dispatch(service, method, args, win)
                        GLib.idle_add(reply, message_id, True, value)
                    except Exception as exc:
                        GLib.idle_add(reply, message_id, False, {"message": str(exc)})
                threading.Thread(target=worker, daemon=True).start()
            except Exception as exc:
                print("[Aurora] rejected bridge message:", exc, flush=True)
        manager.connect("script-message-received::chimera", on_message)
    else:
        print("[Aurora] native bridge disabled for non-packaged URI", flush=True)

    view.load_uri(uri)

    def on_key(_widget, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and event.keyval in (Gdk.KEY_q, Gdk.KEY_Q):
            Gtk.main_quit()
            return True
        if ctrl and event.keyval in (Gdk.KEY_r, Gdk.KEY_R):
            view.reload()
            return True
        return False

    def request_fullscreen():
        if win.get_realized():
            win.fullscreen()
            win.present()
        return GLib.SOURCE_REMOVE

    win.add(view)
    win.connect("key-press-event", on_key)
    win.connect("destroy", Gtk.main_quit)
    win.connect("map-event", lambda *_args: GLib.idle_add(request_fullscreen))
    win.show_all()
    win.present()
    GLib.idle_add(request_fullscreen)
    Gtk.main()

if __name__ == "__main__":
    main()
