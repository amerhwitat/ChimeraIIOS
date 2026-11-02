#!/usr/bin/env python3
"""Aurora kiosk shell: renders the project's HTML desktop fullscreen."""
import os
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, Gdk, WebKit2, GLib  # noqa: E402

DEFAULT_URI = "file:///opt/aurora/desktop/index.html"


def main():
    uri = os.environ.get("AURORA_DESKTOP_URI") or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI)
    win = Gtk.Window()
    win.set_title("Aurora Desktop")
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_keep_above(False)
    view = WebKit2.WebView()
    try:
        s = view.get_settings()
        s.set_property("allow-file-access-from-file-urls", True)
        s.set_property("allow-universal-access-from-file-urls", True)
        s.set_property("enable-write-console-messages-to-stdout", True)
        s.set_property("hardware-acceleration-policy", WebKit2.HardwareAccelerationPolicy.NEVER)
        s.set_property("enable-smooth-scrolling", True)
        s.set_property("enable-accelerated-2d-canvas", False)
        s.set_property("enable-webgl", False)
    except Exception as exc:  # pragma: no cover - defensive
        print("settings warning:", exc, flush=True)
    view.load_uri(uri)

    def on_key(_w, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        if ctrl and event.keyval in (Gdk.KEY_q, Gdk.KEY_Q):
            Gtk.main_quit()
            return True
        if ctrl and event.keyval in (Gdk.KEY_r, Gdk.KEY_R):
            view.reload()
            return True
        return False

    win.add(view)
    win.connect("key-press-event", on_key)
    win.connect("destroy", Gtk.main_quit)
    win.fullscreen()
    win.show_all()
    win.present()
    Gtk.main()


if __name__ == "__main__":
    main()
