# Hosted and BareMetal platform compatibility

This document is the authoritative cross-platform boundary for the two core delivery editions: **Hosted** and **BareMetal**.

## Edition distinction

- **Hosted** runs Chimera user-space tools on an existing Linux, FreeBSD, Windows or macOS installation. It uses the host's process, filesystem, network and service APIs through adapters; it does not replace the host kernel.
- **BareMetal** boots Koronos directly. Linux, FreeBSD, Windows and macOS are build, packaging and flashing environments only. Their kernel drivers and service managers are not imported into Koronos.

## Host support matrix

| Host | Hosted edition | BareMetal build/flash | Native integration boundary |
|---|---|---|---|
| Linux | User-space bridge supported | Supported | systemd/OpenRC lifecycle adapter (runit/s6/SysV detection remains a future adapter); POSIX/Linux APIs |
| FreeBSD | POSIX adapter partial | Supported when toolchain is present | FreeBSD rc.d/sysrc, kqueue, PF, routing sockets; no Linux netlink assumptions |
| Windows 10/11 | User-space bridge supported | WSL or native LLVM/MSVC tooling | SCM, Winsock, Windows paths and process APIs |
| macOS | User-space bridge supported | Supported when toolchain is present | launchd, Darwin/BSD sockets, APFS-aware paths |

## Host service lifecycle

The portable host service utility is installed as `chimera-host-services`. It dispatches to systemd/OpenRC on Linux, rc.d/sysrc on FreeBSD, Windows Service Control Manager on Windows, and launchctl on macOS. It lists and inspects services without elevation; lifecycle mutations require `--apply`, an explicit confirmation phrase and administrator privileges for system services. Package installation remains a separate, distribution-specific operation.

## Compatibility rules

1. Resolve the host OS and architecture at runtime; never infer Linux from a POSIX shell.
2. Use native APIs for service management, process creation, path conversion, networking and notifications.
3. Unsupported APIs return a typed unsupported result; do not silently substitute a command from another OS.
4. Never load Windows, Linux, FreeBSD or macOS kernel drivers into Koronos.
5. Never claim foreign executable compatibility merely because a PE, ELF or Mach-O parser exists.
6. Host route and service mutations require explicit administrator consent and audit records.
7. BareMetal hardware support requires a matched native Koronos driver or a supported firmware interface.

## API parity roadmap

- Process: launch, terminate, environment, exit status, bounded stdout/stderr.
- Filesystem: metadata, permissions, symlinks, atomic replacement, removable volumes.
- Networking: interface discovery, dual-stack sockets, route read/modify, firewall integration.
- Services: discovery, status, install, enable/disable, lifecycle operations.
- Desktop: host-native open/launch, clipboard and display capability negotiation.
- Security: privilege broker, audit, code-signing and platform sandbox integration.

A listed API category is a contract target, not a statement that every operation is already implemented. Use `system/platform/compatibility-contract.json` and `system/baremetal/compatibility-matrix.json` for machine-readable support levels.

## Production blockers

The x86-64 IDT/interrupt path, syscall privilege transitions and SMP/IPI implementation remain separate BareMetal production blockers. Cross-platform Hosted work must not bypass these gates.
