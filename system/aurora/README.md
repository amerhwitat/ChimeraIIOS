# Aurora System Log Window

Aurora's system-monitor contract provides one always-available diagnostic window for Live CD, Installer and installed Chimera II OS sessions.

It combines:
- boot/Koronos messages;
- installer phase messages;
- hardware and driver discovery;
- service activity;
- real-time process/thread snapshots;
- CPU/load information;
- persistent logs after installation.

The graphical provider should consume `system/aurora/chimera-log-window.json`. Early boot and recovery environments use the terminal-compatible monitor scripts instead.
