#!/usr/bin/env python3
"""Aurora Network Applications panel; launches only installed, fixed commands."""
import shutil
import subprocess
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


APPS = [
    ("NetworkManager", "Connection and device status", "nmcli", ["device", "status"], "inspect"),
    ("IP configuration", "Interfaces and addresses", "ip", ["-brief", "address"], "inspect"),
    ("Routing table", "Kernel routes", "ip", ["route", "show"], "inspect"),
    ("Listening sockets", "TCP/UDP listeners", "ss", ["-tulpn"], "inspect"),
    ("DNS lookup", "Resolve a hostname", "dig", ["+short"], "target"),
    ("Ping", "Check reachability of a host", "ping", ["-c", "4"], "target"),
    ("Nmap", "Scan only a network you are authorized to assess", "nmap", ["-sV", "-T3"], "target-terminal"),
    ("SMB client", "Access an authorized SMB share", "smbclient", [], "target-terminal"),
    ("NFS exports", "Show exports from an authorized NFS server", "showmount", ["-e"], "target-terminal"),
    ("SSH", "Open a remote shell", "ssh", [], "target-terminal"),
    ("SFTP", "Open a secure file-transfer session", "sftp", [], "target-terminal"),
]

class NetworkApplications(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.chimera.AuroraNetworkApplications")

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("Aurora · Network Applications")
        win.set_default_size(760, 560)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_border_width(18)
        heading = Gtk.Label()
        heading.set_markup("<span size='x-large' weight='bold'>Network Applications</span>\nAuthorized local and intranet tools")
        heading.set_xalign(0)
        outer.pack_start(heading, False, False, 0)
        self.target = Gtk.Entry()
        self.target.set_placeholder_text("Optional host / IP / share (required for target-based tools)")
        outer.pack_start(self.target, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        for i, (name, desc, command, args, mode) in enumerate(APPS):
            row, col = divmod(i, 2)
            button = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            title = Gtk.Label(label=name); title.set_xalign(0)
            detail = Gtk.Label(label=desc); detail.set_xalign(0)
            detail.set_line_wrap(True)
            box.pack_start(title, False, False, 0); box.pack_start(detail, False, False, 0)
            button.add(box)
            installed = shutil.which(command)
            button.set_sensitive(bool(installed))
            button.set_tooltip_text(f"{command} is not installed" if not installed else f"Run {command} using fixed argument handling")
            button.connect("clicked", self.launch, name, command, args, mode)
            grid.attach(button, col, row, 1, 1)
        scroll.add(grid); outer.pack_start(scroll, True, True, 0)
        scope = Gtk.Label(label="Use these tools only on systems and networks you own or are authorized to assess.")
        scope.set_xalign(0); scope.set_line_wrap(True)
        outer.pack_start(scope, False, False, 0)
        win.add(outer); win.show_all()

    def launch(self, _button, name, command, args, mode):
        target = self.target.get_text().strip()
        if mode in ("target", "target-terminal") and not target:
            self.message("Enter a host, IP address or share in the target field first.")
            return
        argv = [command, *args]
        if mode in ("target", "target-terminal"):
            argv.append(target)
        if mode == "target-terminal":
            terminal = shutil.which("foot") or shutil.which("xterm")
            if not terminal:
                self.message(f"{name}: install foot or xterm to run this interactive tool.")
                return
            argv = [terminal, "-e", *argv]
        try:
            if mode == "inspect":
                result = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=12)
                self.message((result.stdout or result.stderr or f"{name}: exited {result.returncode}")[:12000])
            else:
                subprocess.Popen(argv, start_new_session=True, close_fds=True)
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.message(f"{name}: {exc}")

    def message(self, text):
        dialog = Gtk.MessageDialog(parent=self.get_active_window(), flags=Gtk.DialogFlags.MODAL,
                                   message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                   text="Aurora Network Applications")
        dialog.format_secondary_text(text)
        dialog.run(); dialog.destroy()

if __name__ == "__main__":
    NetworkApplications().run(None)
