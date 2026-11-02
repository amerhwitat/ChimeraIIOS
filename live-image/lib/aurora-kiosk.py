#!/usr/bin/env python3
"""Aurora kiosk shell: render the project's HTML desktop across the full display."""
import os
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, Gtk, GLib, WebKit2  # noqa: E402

DEFAULT_URI = "file:///opt/aurora/desktop/index.html"


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

    view = WebKit2.WebView()
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
        # EWMH fullscreen requests are handled by the window manager. Run after
        # the window is mapped so the WM can apply the state before first paint.
        if win.get_realized():
            win.fullscreen()
            win.present()
        return GLib.SOURCE_REMOVE

    win.add(view)
    win.connect("key-press-event", on_key)
    win.connect("destroy", Gtk.main_quit)
    win.connect(
        "map-event",
        lambda *_args: GLib.idle_add(request_fullscreen),
    )
    win.show_all()
    win.present()
    GLib.idle_add(request_fullscreen)
    Gtk.main()


if __name__ == "__main__":
    main()
