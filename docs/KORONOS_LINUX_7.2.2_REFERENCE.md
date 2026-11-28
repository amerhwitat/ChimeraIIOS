# Koronos architecture map against Linux v7.2.2

## Pinned upstream reference

- Requested source browser: https://elixir.bootlin.com/linux/v7.2.2/source
- Stable source tag: `v7.2.2`
- Tag commit prefix: `52c36105f76e` (the reference-build workflow verifies this prefix)
- Kernel source repository: https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
- Upstream release archive: https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.2.tar.xz
- Release date: 2026-08-28
- License: GPL-2.0-only for the Linux kernel source.

The Linux source is a behavioral and architectural reference for Koronos. The reference-build workflow compiles a separate Linux x86_64 `bzImage`, builds static BusyBox 1.37.0, assembles a minimal initramfs, and boots that pair in QEMU. Those Linux artifacts are reference evidence; they are not silently copied into the Koronos kernel or the Chimera ISO.

## Source-to-subsystem map

| Concern | Linux v7.2.2 source paths | Koronos implementation area | Required contract to preserve |
|---|---|---|---|
| Boot and PID 1 | `init/main.c`, `kernel/fork.c`, `kernel/exit.c` | `kernel/core/koronos.cpp`, `kernel/core/target_launch.cpp`, `kernel/targets/*_init.c` | Kernel creates a real process context, launches init, retains PID 1, and supervises its descendants. |
| Scheduler and run queues | `kernel/sched/core.c`, `kernel/sched/fair.c`, `include/linux/sched.h` | `kernel/core/scheduler.cpp`, `kernel/core/thread.cpp`, `kernel/core/preemptive_sched.cpp` | Ready/runnable state, wakeups, blocking, priority, CPU ownership, run-queue locking, and a real dispatch path must be integrated—not just callback invocation. |
| x86-64 entry and context | `arch/x86/entry/entry_64.S`, `arch/x86/kernel/process_64.c`, `arch/x86/include/asm/switch_to.h` | `kernel/arch/x86_64/interrupts.asm`, `kernel/arch/x86_64/context_switch.asm`, `kernel/core/preemptive_sched.cpp` | Preserve the complete architectural register frame, stack alignment, privilege transition, per-task kernel stack, address-space switch, and correct IRET/sysret return path. |
| Syscall ABI | `arch/x86/entry/syscalls/syscall_64.tbl`, `arch/x86/entry/common.c`, `kernel/sys.c` | `kernel/core/syscall.cpp`, `kernel/include/chimera/koronos_abi.h`, `kernel/core/target_launch.cpp` | Validate syscall number and user pointers, preserve ABI registers, check CPL/CR3 ownership, and return errors without corrupting task state. |
| Page faults and VM | `arch/x86/mm/fault.c`, `mm/memory.c`, `mm/mmap.c`, `mm/page_alloc.c` | `kernel/core/address_space.cpp`, `kernel/core/process_loader.cpp`, `kernel/core/frame_allocator.cpp` | Resolve only valid mappings, enforce user/supervisor and W^X permissions, handle COW/demand faults if supported, and roll back partial map operations. |
| VFS and pathname lookup | `fs/namei.c`, `fs/open.c`, `fs/read_write.c`, `fs/file_table.c`, `fs/dcache.c`, `include/linux/fs.h` | `kernel/core/initramfs_fs.cpp`, `kernel/core/native_stack.cpp` | Separate mount, dentry/path, inode, file-description, descriptor, permissions, lifetime, and block-cache semantics. A marker-sector test is not a general VFS. |
| SMP and CPU lifecycle | `arch/x86/kernel/smpboot.c`, `kernel/smp.c`, `kernel/sched/core.c` | `kernel/core/smp.cpp`, `kernel/core/scheduler.cpp` | AP startup is only the first gate; production SMP also needs per-CPU scheduler state, remote wakeup/IPI handling, migration, locking, and race-safe task ownership. |
| Storage and block layer | `block/blk-core.c`, `drivers/block/virtio_blk.c`, `drivers/virtio/virtio_pci_modern.c` | `kernel/core/native_stack.cpp`, `kernel/core/install_recovery.cpp` | Queue ownership, request completion, timeouts, DMA constraints, flush/barrier semantics, partition discovery, and a real filesystem implementation. |
| Desktop display/input | `drivers/gpu/drm/*`, `drivers/input/*`, `drivers/hid/*`, `drivers/tty/*` | `desktop/aurora/*`, `kernel/core/device.cpp`, display/input drivers | Kernel display/input device support must feed a compositor; artwork and component profiles are not a running desktop session. |

Linux's `Documentation/core-api/entry.rst` is particularly useful for the ordering of entry/exit state transitions (lockdep, RCU/context tracking, tracing, preemption accounting) and its `noinstr` restrictions. The VFS documentation in `Documentation/filesystems/vfs.rst` describes the separation between superblocks, inodes, dentries, files, and mount/path state.

## Current Koronos source facts that shape the implementation

These are deliberate boundaries, not claims of parity with Linux:

1. `kernel/core/scheduler.cpp` remains a callback scheduler. `chimera_sched_run_once()` executes callbacks synchronously, and `chimera_sched_run_parallel()` returns zero. The separate x86-64 kernel-task preemption self-test does not yet make this the public process scheduler.
2. `kernel/core/process.cpp` admits and tracks ELF image metadata/state. It does not yet provide a complete scheduler-owned process lifecycle with context save/restore, parent/child wait, signal/fault exit, address-space switch, and resource reclamation.
3. `kernel/core/target_launch.cpp` enters a ring-3 init payload synchronously. Its own comments correctly state that PID 1 remains in the occupied entry and does not yet provide scheduling or child supervision.
4. `kernel/core/native_stack.cpp` contains real legacy virtio-blk I/O and a custom Koronos test-volume mount/persistence check. Its child exit/reap model is a synchronous callback test, not a scheduled child process. The destructive disk test is now opt-in via a dedicated Multiboot2 module; ordinary boots must leave disks untouched.
5. `kernel/core/install_recovery.cpp` exercises a four-phase journal/rollback/metadata-restore state machine on a tiny synthetic Koronos test volume. It does not partition arbitrary disks, mount ext4/FAT, or provide a general user-facing installer/recovery application.
6. `kernel/targets/live_init.c` is a ring-3 text console; `installer_init.c` is a dry-run report; `recovery_init.c` is diagnostics-only. None is a complete graphical desktop session.

## Windows reference handling

`W2K-ASM Notepad.txt.pdf` is used only to compare high-level mechanisms:

- Pages 248–261: dispatcher/ready-queue selection, `KiSwapThread`, `SwapContext`, kernel stack and address-space switching.
- Pages 417–418: system-service table selection, bounds checking, and syscall argument handling.
- Pages 472–474: page-fault address capture and access/privilege validation.

This is architectural study material, not a source-code donor. Do not copy proprietary Windows implementation code. Implement original Koronos C/C++/ASM with independent provenance and tests.

## Linux licensing and provenance

Linux kernel source is GPL-2.0-only. This project uses its algorithms, contracts, and public interfaces as design references and writes original Koronos code. If any Linux source is copied or adapted directly, record the exact upstream path, commit, copyright/license notices, and comply with GPL-2.0 obligations before distributing the derivative. Do not mix Linux code into a differently licensed component without a deliberate license review.

## Current Aurora/Wayland implementation gap

A source-tree check found that `desktop/aurora/wayland/aurora_wayland_backend.hpp` exists, but its included `aurora_desktop.hpp` and the referenced `aurora_wayland_backend.cpp` implementation are absent from the source tree. The Developer Guide contains an old illustrative implementation, but it is not production-safe to copy as-is: it loses the distinction between backend and surface user data, does not retain surface ownership in the backend map, leaves pointer/keyboard resources unbound, and has no usable shared-memory buffer/output/xdg-shell pipeline. It is a design note, not a compilable compositor.

`desktop/native/chimera-desktop-shell.cpp` is a GTK host shell client. It is not a Wayland compositor and cannot run directly on Koronos. The current `kernel/targets/live_init.c` is a ring-3 text console. A real native Aurora session still requires:
- A compilable compositor core and a retained surface/resource lifetime model.
- `wl_shm` or DMA-BUF buffer import, damage tracking, output globals, frame callbacks, and xdg-shell roles.
- Seat/pointer/keyboard resource ownership and real input-event delivery.
- DRM/KMS or framebuffer presentation, modesetting, synchronization, and fallback.
- Kernel process scheduling and graphics/input service APIs so the compositor and shell can run as ordinary user processes.
- A session manager, launcher, terminal, file manager, and logout/shutdown lifecycle.

The desktop compatibility workflow's GTK/OpenGL/OpenCV tests are host/component checks; they do not close these native compositor or Koronos runtime gates.

## Desktop source references

For compositor and protocol work, use the upstream [Wayland](https://gitlab.freedesktop.org/wayland/wayland), [wayland-protocols](https://gitlab.freedesktop.org/wayland/wayland-protocols), and [Weston](https://gitlab.freedesktop.org/wayland/weston) source trees. For the Linux-side device contracts, trace DRM/KMS and evdev/input in the pinned kernel source. A successful OpenGL/OpenCV component build or an Aurora artwork/media check is not evidence that a native compositor, shell, session manager, and applications have started.

## Build evidence boundaries

The Linux reference workflow is expected to prove:

- Pinned Linux v7.2.2 source checkout and x86_64 kernel `bzImage` build.
- Static BusyBox 1.37.0 build and initramfs creation.
- QEMU boot reaching Linux PID 1 and a working BusyBox shell.

It does **not** claim a complete Linux distribution, graphical Linux desktop, or Linux payload shipped in ChimeraIIOS. Koronos and Chimera acceptance remain separate gates, and the release manifest must not be promoted until production userspace and desktop gates pass.
