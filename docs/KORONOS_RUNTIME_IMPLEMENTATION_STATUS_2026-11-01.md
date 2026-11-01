# Koronos runtime implementation and Linux/Arch parity status — 2026-11-01

## Scope and evidence

This status covers the ChimeraIIOS and OctavianOS runtime remediation branches. It distinguishes code that is now present from runtime paths that still lack evidence.

## Implemented in these branches

- Ported Octavian's x86-64 frame allocator, page-table/address-space backend, target ELF loader/launcher, TSS/RSP0 setup, SYSCALL entry/return and timeout-abort assembly into ChimeraIIOS.
- Exported the bootstrap PML4 symbol used by the isolated address-space implementation.
- Added a bounded CPIO-newc parser with regular-file and directory metadata, path traversal rejection, duplicate-path rejection, bounds checking, and CRC checking for 070702 archives.
- Added a small read-only initramfs VFS with bounded file and descriptor tables, descriptors 0–2 reserved for standard streams, OPEN/READ/WRITE/SEEK/CLOSE kernel APIs, and a bounded in-memory /tmp overlay.
- Routed native ring-3 OPEN, READ, WRITE, SEEK, and CLOSE syscalls through active-process context validation and page-table user-range checks.
- Added target-specific Live, Installer and Recovery initramfs module identities. The boot builder now emits uncompressed CPIO-newc archives alongside gzip archives; ISO staging and GRUB entries pass the raw CPIO module to Koronos.
- The kernel mounts Live and Recovery CPIO archives in the early VFS path, and mounts the Installer CPIO archive in the installer task. If a production init ELF is absent, the kernel explicitly withholds userspace readiness.
- Added host-side CPIO/VFS tests for /etc/os-release reads, seeking, close, /tmp writes and path traversal rejection. Added target-specific module-classification coverage.

## Current CI evidence

- ChimeraIIOS Koronos ELF build, ELF validation, protected-process admission, and unresolved-symbol checks passed: https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41329536903.
- ChimeraIIOS process-loader, module-classification, CPIO VFS, handoff-verifier and freestanding build tests passed: https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41329536872.
- ChimeraIIOS QEMU boot matrix was still running at the last inspection: https://github.com/amerhwitat/ChimeraIIOS/actions/runs/41329536879.
- OctavianOS native Koronos build and expanded CPIO checks were running: https://github.com/amerhwitat/OctavianOS/actions/runs/41329625837.
- The earlier six-case candidate run #41328996560 failed all six cases before the CPIO module was added to the acceptance ISO. The revised acceptance payload now supplies a CPIO root and the ring-3 smoke program exercises file syscalls; that revised matrix still requires a fresh completed result.

## Remaining production blockers

- The initramfs VFS is a bounded bootstrap implementation, not Linux's full VFS: there is no dentry/inode cache, mount namespace, permissions/ownership enforcement, symlink resolution, page cache, block-backed filesystem driver, or persistent root filesystem.
- The descriptor table is currently global to the single bootstrap init, not owned by independently scheduled processes. The /tmp overlay is bounded RAM storage, not a persistent tmpfs implementation with full POSIX semantics.
- The production boot images still do not contain a supported target-specific native USER_INIT_ELF wired to the real Live, Installer and Recovery initramfs. The existing CPIO mounts do not themselves start /init, a shell, a desktop, or a service manager.
- General process creation, per-task register/kernel-stack/address-space switching, blocking wait/reap, signals, pipes, robust exit teardown, and multi-process scheduling remain incomplete.
- Service dependency ordering exists as metadata, but there is no production PID 1 service supervisor comparable to systemd: no reliable spawn/monitor/restart/stop lifecycle, readiness protocol for all services, or shutdown transaction.
- AP bring-up and measured SMP overlap on at least two CPUs remain unimplemented/unverified.
- Installer disk discovery/partitioning/filesystem creation/persistent install and cold-boot verification remain unimplemented. Recovery repair postconditions remain unverified.
- The user-supplied wallpaper PNG bytes are not yet committed in the repositories or installed in the native desktop image. The artwork manifest/hash gate is present, but the current renderer fallback does not match the supplied image hash; the ISO build correctly fails closed rather than claiming the uploaded artwork is embedded.
- Aurora and Marine web desktop prototypes are not native Wayland compositors/window managers. The native desktop session, compositor, input, GPU and session-service lifecycle require separate runtime verification.

## Linux kernel, Arch Linux and desktop comparison

Linux supplies mature implementations for the VFS, page tables and MMU, ELF/binfmt loading, task scheduling, file descriptor tables, wait/reap, signals, pipes, block and filesystem drivers, initramfs unpacking, SMP/AP bring-up and kernel/user ABI. Koronos now has a small subset of the early boot and single-init filesystem path; it must not be described as Linux parity.

Arch Linux is a distribution on the Linux kernel. Its userspace integration includes systemd as PID 1, systemd service units, udev, package management, filesystem tools, networking and desktop session components. Koronos should implement compatible behavior at its own stable ABI boundaries and reuse audited userspace utilities where licensing and architecture permit, not copy Arch's package database or Linux kernel internals wholesale.

For desktops, Aurora's macOS-inspired global menu/window/dock layout and Marine's Windows-inspired Start/taskbar layout are presentation prototypes. Linux desktop parity requires an actual Wayland compositor, display/input backends, protocol support, session manager, shell, settings daemons, portals, audio, power and accessibility services—not merely HTML/CSS screens.

## Release decision

Keep both pull requests draft and the production release gate closed. Do not publish or label an ISO as production until the revised six-case production-init ELF matrix, real root/VFS syscalls, desktop startup, installer persistence, recovery repair, and SMP evidence all pass on the same ISO SHA-256.
