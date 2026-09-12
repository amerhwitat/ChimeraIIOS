# Services compatibility

Aurora/Koronos expose a capability model instead of cloning another operating system's service manager. The common service state machine is `inactive -> starting -> active -> stopping -> inactive`, with a `failed` state that can return to `starting` after policy-controlled recovery.

Backends include Linux systemd/D-Bus/NetworkManager/PipeWire/CUPS/udev/Samba, Windows SCM/Task Scheduler/PowerShell/Windows Terminal/WSL/native networking, and macOS launchd/POSIX/CoreAudio/WebKit/printing boundaries. A backend may report `unsupported` rather than emulate a privileged feature unsafely.

No adapter installs a service or loads kernel code implicitly. Driver installation remains under `drivers/` security and provenance rules.
