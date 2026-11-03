#!/usr/bin/env python3
"""Aurora kiosk shell with a restricted native keyboard-layout bridge."""
import json
import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, Gtk, GLib, WebKit2  # noqa: E402

DEFAULT_URI = "file:///opt/aurora/desktop/index.html"
XKB_LAYOUTS = {
    "us", "gb", "ara", "il", "fr", "de", "es", "ru", "gr", "tr",
    "ir", "pk", "in", "bd", "jp", "kr", "br", "it", "nl", "pl",
}


def display_geometry():
    """Return the primary monitor geometry, with the X screen as fallback."""
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


def handle_host_message(_manager, result):
    """Accept only the explicit XKB layout allowlist; never execute page text."""
    try:
        raw = result.get_js_value().to_string()
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get("type") != "set-input-layout":
            return
        layout = payload.get("layout")
        if layout not in XKB_LAYOUTS:
            print("[Aurora] rejected unknown keyboard layout", flush=True)
            return
        subprocess.run(
            ["setxkbmap", "-layout", layout],
            check=True,
            timeout=8,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"[Aurora] keyboard layout applied: {layout}", flush=True)
    except (ValueError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print(f"[Aurora] keyboard layout request failed: {exc}", flush=True)


def main():
    uri = os.environ.get("AURORA_DESKTOP_URI") or (
        sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI
    )
    x, y, width, height = display_geometry()
    print(
        f"[Aurora] display={width}x{height} origin={x},{y}; opening {uri}",
        flush=True,
    )

    win = Gtk.Window()
    win.set_title("Aurora Desktop")
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_keep_above(False)
    win.set_default_size(width, height)
    win.set_position(Gtk.WindowPosition.CENTER)

    manager = WebKit2.UserContentManager()
    manager.register_script_message_handler("auroraHost")
    manager.connect("script-message-received::auroraHost", handle_host_message)
    view = WebKit2.WebView.new_with_user_content_manager(manager)
    view.set_hexpand(True)
    view.set_vexpand(True)
    try:
        settings = view.get_settings()
        settings.set_property("allow-file-access-from-file-urls", True)
        settings.set_property("allow-universal-access-from-file-urls", True)
        settings.set_property("enable-write-console-messages-to-stdout", True)
        settings.set_property(
            "hardware-acceleration-policy",
            WebKit2.HardwareAccelerationPolicy.NEVER,
        )
        settings.set_property("enable-smooth-scrolling", True)
        settings.set_property("enable-accelerated-2d-canvas", False)
        settings.set_property("enable-webgl", False)
    except Exception as exc:  # pragma: no cover - defensive
        print("[Aurora] WebKit settings warning:", exc, flush=True)

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
