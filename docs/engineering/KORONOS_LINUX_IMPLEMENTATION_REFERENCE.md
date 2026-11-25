# Koronos runtime implementation map — Linux reference

Status: engineering reference only. This document maps the open Koronos production gaps to upstream Linux design and source locations. It does not claim that the corresponding Linux subsystems, drivers, or userspace packages are implemented in ChimeraIIOS.

Reference baseline: upstream Linux source tree at https://github.com/torvalds/linux and kernel documentation at https://docs.kernel.org/. Prefer the architecture-neutral interfaces and invariants; do not transplant Linux internals without adapting them to Koronos' ABI, memory model, boot protocol, and license obligations. Linux kernel source is GPL-2.0-only.

## Current verified boundary

At PR #320 head `a6888c0219fccb5ae3636811304a4d0a71a84b21`:
- The scheduler is a cooperative callback dispatcher. It has no resumable architecture context, independent kernel stacks, timer preemption, or real parallel dispatch.
- The scheduler online CPU count is intentionally restricted to the bootstrap CPU. AP startup and measured CPU overlap are absent.
- The target launcher maps a bounded read-only newc archive into a RAM namespace and enters one ring-3 init ELF. This is not a persistent block-backed VFS or a general mount namespace.
- The init payload's resident wait loop preserves a PID 1-like task but does not schedule or supervise children.
- Installed-root handoff, installer disk transaction/rollback, and recovery filesystem repair are not established.
- Desktop artwork/browser previews and compatibility tests do not establish native compositor sessions.
- Catalogue metadata and selected command/ISA tests do not establish complete provider conformance.
- The six-case Live/Installer/Recovery × BIOS/UEFI acceptance evidence is absent. The production publish job must remain blocked.

## Implementation sequence and Linux references

### 1. x86-64 context switching and timer preemption

Linux references:
- x86-64 entry/interrupt assembly: https://github.com/torvalds/linux/tree/master/arch/x86/entry
- x86 process state and switch code: https://github.com/torvalds/linux/blob/master/arch/x86/kernel/process_64.c
- Generic scheduler core: https://github.com/torvalds/linux/blob/master/kernel/sched/core.c
- Scheduler design documentation: https://docs.kernel.org/scheduler/index.html
- x86 entry documentation: https://docs.kernel.org/arch/x86/entry_64.html

Koronos work:
1. Define a documented, aligned x86-64 kernel context ABI (callee-saved registers, RSP, RIP, flags, FS/GS state as required).
2. Add assembly save/restore and first-run trampoline; give every kernel thread an independently allocated, guarded stack.
3. Separate interrupt entry frames from voluntary switch frames; define interrupt return and syscall return invariants.
4. Connect a calibrated local-APIC timer interrupt to a scheduler tick and safe reschedule point; preserve interrupt nesting and preemption counts.
5. Implement task lifecycle, block/wake, wait/reap and address-space ownership before scheduling user tasks.
6. Add deterministic host tests for context-frame layout plus QEMU tests for two independently progressing tasks, timer preemption, blocking/wakeup, exit/reap, and address-space isolation.

Do not call callback stepping or a timer counter “preemption.” Require observed register/stack restoration and a timer-driven task switch in the trace.

### 2. AP startup and SMP

Linux references:
- SMP core: https://github.com/torvalds/linux/blob/master/kernel/smp.c
- x86 SMP boot: https://github.com/torvalds/linux/tree/master/arch/x86/kernel
- CPU hotplug: https://github.com/torvalds/linux/blob/master/kernel/cpu.c
- x86 APIC: https://github.com/torvalds/linux/tree/master/arch/x86/kernel/apic

Koronos work:
1. Discover enabled processors from ACPI MADT (with a documented fallback only where justified).
2. Start APs through the x86-64 INIT/SIPI sequence and a low-memory trampoline; establish per-CPU GDT/TSS, IDT, interrupt controller state and stacks.
3. Publish a CPU online state only after each AP acknowledges its per-CPU initialization.
4. Add per-CPU run queues, locking/ordering rules, wakeup IPIs and load balancing.
5. Prove simultaneous execution using per-CPU counters and timestamped overlap windows under QEMU with at least two vCPUs; keep BSP-only reporting until then.

### 3. Block devices and persistent VFS

Linux references:
- Block layer: https://github.com/torvalds/linux/tree/master/block
- blk-mq design: https://docs.kernel.org/block/blk-mq.html
- Driver model: https://github.com/torvalds/linux/tree/master/drivers/base
- VFS overview: https://docs.kernel.org/filesystems/vfs.html
- Mount API: https://github.com/torvalds/linux/tree/master/fs
- Device tree/ACPI and PCI: https://github.com/torvalds/linux/tree/master/drivers

Koronos work:
1. Define block-device registration, capacity, logical/physical sector sizes, bounded request queues, completion/error semantics and flush/barrier semantics.
2. Implement and test at least the selected virtual-machine driver (virtio-blk is a useful first target), then AHCI/NVMe as separately scoped drivers.
3. Add PCI enumeration, DMA-safe buffers, IOMMU/DMA constraints where applicable, interrupt and timeout handling.
4. Implement GPT/MBR discovery and partition bounds checks.
5. Define VFS superblock, inode, dentry, file, mount namespace and per-process descriptor ownership.
6. Bring up one persistent filesystem backend (e.g. FAT for a simple first writable target or ext2 as a learning target) with crash-consistency and read/write tests; add other filesystems only with real implementations.
7. Keep initramfs read-only and RAM /tmp as explicit temporary mounts, not substitutes for persistent storage.

Acceptance: write, flush, reboot, remount, and read back known data; test malformed partition tables, I/O errors, short reads, and concurrent access.

### 4. Persistent PID 1, process supervision and installed-root handoff

Linux references:
- Early init and kernel startup: https://github.com/torvalds/linux/blob/master/init/main.c
- Process creation and exit: https://github.com/torvalds/linux/tree/master/kernel
- exec implementation: https://github.com/torvalds/linux/tree/master/fs
- initramfs/root switching documentation: https://docs.kernel.org/admin-guide/initrd.html
- PID namespaces and process lifecycle: https://docs.kernel.org/

Koronos work:
1. Replace synchronous one-shot target entry with scheduler-owned process objects and durable PID/parent/child relationships.
2. Implement exec, wait, exit, signal delivery, zombie reaping, descriptor tables and address-space teardown.
3. Build PID 1 as a real user process that launches, monitors, restarts or reports child services according to explicit policy.
4. Implement root discovery, filesystem integrity checks, mount namespace setup and an atomic, rollback-safe switch from initramfs to installed root.
5. Test PID 1 survival, child crash/restart, orphan adoption/reaping, mount failure rollback and cold boot from installed media.

### 5. Installer and recovery storage transactions

Linux references:
- Block/partition interfaces: https://github.com/torvalds/linux/tree/master/block
- Filesystem and mount interfaces: https://github.com/torvalds/linux/tree/master/fs
- Device discovery: https://github.com/torvalds/linux/tree/master/drivers
- Filesystem checking tools are userspace utilities, not kernel VFS substitutes: https://github.com/util-linux/util-linux and https://github.com/e2fsprogs/e2fsprogs

Koronos work:
1. Installer: enumerate disks, require explicit target confirmation, validate partition plans, create partitions/filesystems, stage files, fsync, verify hashes, install bootloader and commit a durable transaction journal.
2. Add power-loss recovery and rollback at every transaction boundary; never overwrite the running source device by default.
3. Recovery: identify supported filesystem types, run the matching real checker/repair tool or native implementation, preserve logs, verify postconditions, and require explicit destructive-repair consent.
4. Test with disposable QEMU disk images, injected I/O failures and power-cut points; verify data and partition tables after reboot.

### 6. Native graphics and desktop sessions

Linux references:
- DRM/KMS: https://github.com/torvalds/linux/tree/master/drivers/gpu/drm
- Input subsystem: https://github.com/torvalds/linux/tree/master/drivers/input
- Mesa: https://gitlab.freedesktop.org/mesa/mesa
- Wayland protocol: https://gitlab.freedesktop.org/wayland/wayland
- Weston reference compositor: https://gitlab.freedesktop.org/wayland/weston
- X.Org server: https://gitlab.freedesktop.org/xorg/xserver

Koronos/Chimera work:
1. Deliver a real framebuffer/DRM-style display backend, input event path, GPU/2D acceleration policy and mode-setting tests.
2. Build or integrate a real compositor and session manager; browser/WebGL mockups remain previews only.
3. Bring up Aurora, Marine, FreeXP and FreeWin11 as separately tested sessions with actual launch, input, rendering, shutdown and crash recovery.
4. Keep compatibility artwork and desktop catalogue metadata separate from runtime readiness.

### 7. Command and ISA provider conformance

Linux references:
- Linux syscall ABI and syscall tables: https://github.com/torvalds/linux/tree/master/arch/x86/entry/syscalls
- ELF and dynamic loader interfaces: https://github.com/torvalds/linux/tree/master/fs
- GNU binutils: https://sourceware.org/binutils/
- LLVM: https://github.com/llvm/llvm-project

Koronos work:
1. For every catalogue command, record the provider (native implementation, verified upstream binary, or explicitly unsupported); no placeholder executables.
2. Test observable behavior, exit codes, signals, options, filesystem semantics and dependency closure against documented compatibility targets.
3. For each claimed ISA, require a real decoder/executor or a named external provider, versioned test corpus and differential/conformance results.
4. Mark unsupported architectures and commands honestly; do not infer support from database rows or toolchain availability.

### 8. Six-case release acceptance

Require the same immutable ISO digest across Live, Installer and Recovery on BIOS and UEFI; retain independently captured firmware traces and artifact provenance. Each trace must show kernel readiness, a genuine CPL3 init syscall, matching userspace readiness, a resident supervised PID 1, and the target-specific postcondition. Separately attach scheduler/preemption/SMP, persistent storage, installed-root, installer, recovery, desktop and provider test evidence.

The release verifier's booleans and trace strings are assertions, not provenance. Preserve the verifier's fail-closed behavior, but add authenticated CI/hardware-run provenance (signed attestations or equivalent immutable run metadata) before accepting external evidence. Never synthesize traces or manifests to make the gate pass.

## Recommended execution order

1. x86-64 context ABI + assembly switch + guarded stacks + timer-preemption test.
2. AP trampoline + per-CPU initialization + measured two-vCPU overlap.
3. virtio-blk + GPT + VFS core + one persistent filesystem.
4. Process lifecycle + descriptor tables + supervised PID 1.
5. Installed-root handoff, then installer transaction and recovery repair.
6. Native graphics/input/compositor and four real sessions.
7. Command/ISA provider inventory and conformance.
8. Authenticated six-case acceptance and only then production publication.

Each milestone must be a code change with focused regression tests, full hosted CI, and (where hardware behavior is claimed) actual QEMU or physical-machine traces. Documentation, contracts, manifests and catalogue metadata do not close implementation gates.
