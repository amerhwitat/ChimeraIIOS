# Open-source integration plan: native services, live desktop and installer

This document separates upstream design reuse from license-compatible source reuse. It does not assert that a referenced project has been imported or that its functionality is already available in Koronos.

## Upstream engineering patterns

- **Virtio/block I/O:** use the Linux kernel's documented virtio transport and virtqueue lifecycle as an architectural reference: device discovery, feature negotiation, queue setup, DMA ownership, completion, reset, error reporting, and flush semantics. Implement against the Virtio specification with Koronos-owned code and tests. Do not copy Linux kernel implementation files into the project without a separate license-compatibility review; Linux kernel files are commonly GPL-2.0-only.
- **Service manager:** borrow systemd's explicit distinction between dependency requirements and ordering, and its job/failure-state model. Keep the existing Kore ABI, but make service readiness depend on a process-owned health result and explicit dependency graph. Do not treat a registered service or successful start callback as sufficient health.
- **Wayland desktop:** follow Weston/libweston backend separation. First make a headless/nested backend usable for protocol and session tests, then implement the native framebuffer/display and input integration. The existing Aurora shell and artwork are not proof that a Wayland compositor is running.
- **Installer:** use a modular job pipeline similar to Calamares: preflight, target selection, partition plan, filesystem creation, mount, payload deployment, bootloader install, validation, and reboot. Every disk-mutating phase needs explicit confirmation, a transaction log, cancellation/error handling, and post-install boot verification. Verify current upstream code and license before importing source; Calamares' former GitHub mirror is archived and points to Codeberg.
- **Live media:** use the initramfs/live-system separation common to Linux distributions: immutable live root, overlay for volatile writes, explicit persistent-storage opt-in, and shared service/session startup for live and installed systems. The live desktop must boot without modifying the target disk.

## Build order and acceptance gates

1. **Driver lifecycle:** descriptor registration -> device-specific probe -> device-specific start -> observable operations -> shutdown/reset. A driver is RUNNING only after both probe and start succeed. Catalog-only virtio descriptors remain unavailable.
2. **Block device:** implement PCI/virtio feature negotiation, queue and descriptor management, bounded requests, completion interrupts/polling, timeouts, reset/error handling, sector bounds, and flush. Add deterministic mock-device tests and QEMU virtio-blk integration tests.
3. **Persistent filesystem:** select a format only after implementing mount, read/write, metadata, permissions/ownership, fsync/flush propagation, crash-consistency checks, and reboot persistence. Keep RAM VFS tests separate.
4. **Service graph:** mark storage, security, logging, network, Kore orchestration, graphics/session and desktop blocked until actual backends are present. Each service needs a real health operation, dependency-failure behavior, and bounded startup timeout.
5. **Targets:** build separate Live, Installer and Recovery initramfs/rootfs payloads with explicit target marker and executable init. Never reuse the test smoke ELF as production init.
6. **Desktop:** verify input, display mode, compositor process, terminal/window launch, session exit/restart, and screenshot or protocol-based smoke evidence. Aurora UI assets alone do not pass this gate.
7. **Installer and recovery:** run non-destructive QEMU tests first; test partition plans against disposable virtual disks; require confirmation before destructive operations; verify installed boot and recovery repair paths.
8. **Acceptance:** run all six Live/Installer/Recovery x BIOS/UEFI cases, then persistent read/write/permissions/ownership/cold-reboot tests, Aurora handoff, installer completion and genuine AP concurrency. Fail closed on any missing evidence.

## Current limitations

- The native virtio driver descriptors are catalog entries; there is no proven operational virtio block backend in the inspected code.
- The driver descriptor ABI now separates probe from start; existing descriptors with no start callback must remain unavailable.
- The runtime evidence matrix is intentionally marked `not_verified` for all six production target/firmware combinations.
- Do not mark a service `verified` from host unit tests, kernel logs, RAM VFS, ISO composition, or boot smoke alone.
