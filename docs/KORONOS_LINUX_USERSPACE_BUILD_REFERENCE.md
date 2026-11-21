# Koronos Linux userspace and service integration reference

This document defines Linux as the compatibility and implementation reference for Koronos userspace. It is an integration plan, not a claim that these upstream components are already built into a production ISO.

## Reference architecture

| Linux reference | Koronos responsibility | Acceptance evidence |
|---|---|---|
| Linux initramfs /init and switch_root | Boot target selection, temporary root, validated installed-root handoff | Live/Installer/Recovery traces; root identity and mount table; failure rollback |
| systemd PID 1 and unit lifecycle | Native service supervisor with dependency graph, restart policy, readiness, shutdown and reaping | Long-lived PID 1; service start/stop/restart/status; dependency and crash-recovery tests |
| systemd-journald / syslog | Structured kernel and userspace logging | Persistent journal, rotation, monotonic timestamps, crash recovery |
| udev / device manager | Device discovery, stable device identity, hotplug and permissions | PCI/USB/block-device enumeration and hotplug tests |
| D-Bus | Authenticated local IPC and service activation | Peer credentials, policy, activation and disconnect tests |
| logind / seatd | Sessions, seats, VT ownership, device access and power keys | Multi-seat, session switch, lock and suspend/resume tests |
| NetworkManager / systemd-networkd | Link, Wi-Fi, DHCP, DNS, route and VPN lifecycle | Wired/Wi-Fi DHCP and reconnect tests |
| PipeWire / WirePlumber | Audio graph, device routing and session policy | Capture/playback, hotplug, suspend/resume and latency tests |
| Wayland compositor / Xwayland | Native GUI session, display protocol, legacy X11 compatibility | Hardware and software renderer tests; launch and close applications |
| XDG portals / polkit | Sandboxed file chooser, screen capture, notifications and privileged actions | Permission-denial and authorization tests |
| util-linux / coreutils / BusyBox | Boot-critical command suite and compatibility surface | Real executable providers and semantic tests |
| Mesa / EGL / Vulkan loader | OpenGL and graphics acceleration compatibility | Renderer identity, GL conformance and GPU reset tests |

## Recommended staged userspace

1. **Bootstrap:** musl or another explicitly selected libc, BusyBox for early rescue tools, initramfs-tools-style archive generation, ELF loader, /dev, /proc, /sys, /run, /tmp, /etc, /usr, and /var mount policy.
2. **Core services:** Koronos PID 1 and service manager first; then logging, device discovery, IPC, time synchronization, credentials and security policy. Do not run two competing network managers or display managers.
3. **Storage and networking:** block discovery, partition table parsing, filesystem drivers, mount helpers, udev-compatible device events, DNS/DHCP and network policy.
4. **Graphical sessions:** seat/session manager, compositor, input stack, Mesa, PipeWire, portals, polkit agent and desktop shell. Start the display manager only after storage, IPC, device and graphics prerequisites are healthy.
5. **Compatibility:** build selected GNU coreutils, util-linux, procps, grep/sed/awk, bash/dash, package tools and application runtimes from pinned upstream releases. Prefer native Koronos implementations only where a tested compatibility implementation is not available.
6. **Installer and Recovery:** share the same verified block/VFS interfaces as the installed system; installer must partition, format, copy, verify and register a bootable root. Recovery must identify and repair supported filesystems without destructive defaults.

## Build and provenance rules

- Pin every source archive or git commit, record its upstream URL, license, version and SHA-256 in the build manifest.
- Separate host build tools from target binaries. Cross-compile against the target sysroot and reject host ELF leakage.
- Build reproducibly where upstream permits; retain compiler, linker, configure flags and dependency manifests.
- Keep optional network-facing services disabled by default. SSH, SMB/NFS servers, web servers, databases and remote desktop services require explicit administrator enablement.
- Never promote stubs, test ELFs, wrappers that only print success, or a successful compile into a runtime-ready provider.
- Each service needs a real executable, unit/descriptor, dependency policy, privilege boundary, health probe, start/stop test and failure/restart test.
- Each desktop profile must report whether it is a native session, a browser visual profile, or a remote/VM session. Never label a visual mock as a booted native desktop.

## Upstream references

- Linux initramfs and root switching: https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html
- systemd units and service manager: https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html and https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html
- systemd boot process: https://www.freedesktop.org/software/systemd/man/latest/bootup.html
- D-Bus specification: https://dbus.freedesktop.org/doc/dbus-specification.html
- udev: https://www.freedesktop.org/software/systemd/man/latest/udev.html
- Wayland protocol: https://wayland.freedesktop.org/
- XDG desktop entry specification: https://specifications.freedesktop.org/desktop-entry-spec/latest/
- XDG desktop portals: https://flatpak.github.io/xdg-desktop-portal/
- PipeWire: https://pipewire.org/
- Mesa: https://docs.mesa3d.org/
- BusyBox: https://busybox.net/
- musl libc: https://musl.libc.org/
- util-linux: https://github.com/util-linux/util-linux

## Current release boundary

The reference above describes the intended integration and acceptance strategy. The current Koronos target init resident loop is not a process scheduler or a full Linux-like init system. A complete service manager, block/VFS stack, native compositor session, Installer and Recovery storage operations remain separate release gates.
