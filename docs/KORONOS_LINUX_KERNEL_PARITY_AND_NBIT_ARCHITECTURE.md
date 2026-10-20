# Koronos Linux-kernel parity, Linux application ABI, and N-bit execution architecture

**Status: architecture and first ABI-hardening slice proposed; full Linux application compatibility is NOT IMPLEMENTED.** This document separates reusable kernel concepts from Linux-specific ABI obligations. It is not a claim that Linux applications or Linux drivers run on Koronos.

## Linux versus Koronos today

| Layer | Linux kernel's established contract | Koronos current source evidence | Gap / required work |
|---|---|---|---|
| Boot and platform | Architecture entry, firmware tables, memory map, interrupt/timer setup, device model | x86-64 ELF/Multiboot2 entry and platform/firmware probe components | Validate BIOS and UEFI independently; HAL/device probes must report real hardware and failures |
| Address spaces | Per-process MMU mappings, VMAs, faults, mmap/mprotect/munmap, copy-to/from-user | ELF validation/load callbacks exist; process metadata admission is separate from address-space creation | Wire process-owned page tables into the actual scheduler/return path; implement fault handling and teardown |
| Task lifecycle | task/thread creation, clone/fork semantics, exec, wait/reap, signals | Process image admission/state registry; scheduler/task primitives | Real current-task identity, process-owned PID, spawn/exit/wait/reap, blocking/wakeup, signal model |
| Syscall ABI | Stable userspace syscall tables per architecture/ABI, user-pointer validation, defined errno and restart behavior | Compatibility recognizer translates a limited syscall subset; dispatcher currently implements only a small subset | Bind ABI/personality to each process; correct register ABI; validate user pointers; return Linux errno; implement calls only with real backends |
| VFS and descriptors | VFS path lookup, dentries/inodes, mounts, file objects, per-process descriptors, filesystem methods | No demonstrated complete VFS-backed open/read/stat/mount path for PID 1 | CPIO/initramfs-backed read-only VFS first, then file descriptors and persistent filesystem/storage backend |
| Scheduler and timers | Preemptive scheduling, wait queues, timer wakeups, per-CPU run queues and SMP | Scheduler, timer, thread, and parallel-dispatch components exist | Prove actual context switching, blocking/wake semantics, timer interrupts, AP startup and concurrent execution |
| Driver model | Bus discovery, driver binding, resource ownership, DMA/IOMMU, power/error lifecycle | PCI generic, virtio, display and generic driver probes are linked | Probe hardware, safely map resources, DMA isolation, interrupts, lifecycle, and device service IPC |
| Service management | Linux kernel primitives plus user-space init/service manager; not every service runs in kernel space | Kore registry/bootstrap previously marked named services running without real service processes; this branch changes those states to BLOCKED until backends and health checks exist | Separate declared, started, healthy, failed states; launch service processes and require real health checks |
| Linux applications | ELF plus Linux syscall ABI, ELF auxiliary vector, TLS, signals, futexes, procfs, epoll, sockets, dynamic loader, libc expectations | ELF64 loading and syscall recognition are partial; many canonical operations return ENOSYS | A staged compatibility profile and conformance suite, beginning with static single-threaded CLI binaries |
| Graphics and desktop | DRM/KMS or framebuffer, input, IPC, compositor/session and userspace services | Display driver and Aurora assets/components exist | Real display/input driver probe, terminal, IPC, compositor and interactive rendering test |

Reference material: [Linux kernel documentation](https://docs.kernel.org/), [VFS overview](https://docs.kernel.org/filesystems/vfs.html), [scheduler documentation](https://docs.kernel.org/scheduler/), and [driver API guide](https://docs.kernel.org/driver-api/).

## Immediate code change in this branch

The existing Linux syscall number map incorrectly mapped several unrelated calls to canonical IDs (for example, x86-64 `open`/ `close` to undefined IDs and `mprotect` to the native ioctl ID; i386 `brk` and legacy `mmap` were also assigned unrelated canonical IDs). This branch changes the translation table to:

- Translate only explicitly enumerated calls whose semantic IDs exist.
- Leave unsupported calls as `0xFFFFFFFF` so the dispatcher returns the existing fail-closed `-ENOSYS` result.
- Refuse to treat i386 legacy `mmap` as the six-register native `mmap` contract.
- Run a host-side regression executable before the freestanding Koronos build.

This is a safety/ABI correctness improvement, **not** implementation of those syscall backends. In particular, `read`, `write`, `mmap`, `munmap`, `ioctl`, `wait4`, and `arch_prctl` must still return `ENOSYS` until their backing functionality and argument validation exist. A translated number is not an implemented syscall.

## Linux application compatibility plan

1. **Personality and execution ABI:** record architecture, ELF class/machine, Linux ABI (x86-64, i386 compat, later AArch64), syscall entry mechanism, pointer width, calling convention, errno convention, TLS and auxiliary-vector policy in process metadata. Never infer personality solely from the instruction used to enter the kernel.
2. **Process/MM:** create a process-owned address space; validate PT_LOAD ranges, BSS, W^X/NX, user stack, auxiliary vector, ELF interpreter and TLS; add page faults, copyin/copyout, memory maps, and cleanup.
3. **Linux syscall boundary:** preserve canonical native IDs but translate from per-process Linux tables. Add a typed argument layer; reject invalid pointers/length overflow; map internal errors to Linux errno. Implement exit/exit_group and getpid against the actual current process before claiming process compatibility.
4. **VFS first slice:** bounded newc CPIO parser with traversal, duplicate, symlink, size and overflow policy; mount it as a read-only root; implement lookup/stat/open/read/close and per-process FD tables. A successful read of a known file by a ring-3 Linux test binary is the first meaningful milestone.
5. **Scheduler and IPC:** implement blocking wait queues and timer wakeups, then futexes, clone/thread groups, signals, pipes, poll/epoll and Unix sockets in dependency order.
6. **Userland bootstrap:** run a statically linked Linux test executable, then a small init/supervisor and service manager. Keep each service in its own schedulable process with restart policy, health checks, dependency order, logs and resource limits.
7. **Devices and graphics:** expose devices through explicit capability/permission-controlled interfaces; add PCI/virtio storage and input, framebuffer first, then a stable display/input ABI for Aurora.
8. **Conformance gates:** syscall ABI tests; malformed ELF/archive tests; user-pointer fault tests; VFS read tests; process exit/wait tests; timeout and cleanup tests; QEMU BIOS and UEFI; then desktop, installer, recovery and installed-disk boot.

## Service and target layering

### Kernel-space primitives (small, privileged, auditable)
- architecture/HAL and interrupt/timer handling
- physical/virtual memory and address spaces
- task/thread scheduler and synchronization
- process lifecycle and syscall entry/return
- VFS core and filesystem drivers
- device/driver framework, DMA/resource management
- IPC/capabilities and security primitives
- clock, entropy, logging and panic diagnostics

### User-space services (isolated, restartable)
- PID 1 init/supervisor and dependency manager
- device manager and storage/mount manager
- logging service and event/notification broker
- network configuration and network stack services
- authentication/policy service
- terminal/session manager and compositor
- input/audio services
- package/update manager
- installer orchestration and disk writer
- recovery diagnostics/repair toolset

Service manifests are declarations only. The kernel must not set a service to healthy merely because it was registered. A readiness result must be tied to a running service process and a successful health check.

## N-bit virtual CPU without misleading native-support claims

Keep physical ISA execution, ABI bitness, and virtual CPU width as three distinct concepts:

- **Native hardware mode:** the processor's actual supported execution mode (x86-64 is still a 64-bit hardware ISA here).
- **Guest virtual CPU profile:** an emulator/interpreter-defined register width and instruction semantics (8/16/32/64/128/256/512/1024/2048/4096/8192-bit research profiles).
- **Application ABI:** the process's Linux/native personality and pointer/syscall layout, independent of the guest profile.

For widths beyond the physical ISA, do not claim native CPU execution. Route execution through a defined interpreter/JIT/emulator with versioned registers, flags, memory ordering, exceptions, privilege model, device model and serialization. A note section or alternate ELF build is metadata, not a functioning virtual CPU. Linux x86-64 binaries require an x86-64-compatible CPU/translator and Linux syscall personality; they do not become 128–8192-bit Linux binaries because the host process selects a research profile.

## Acceptance gates (fail closed)

- [ ] Host syscall translation regression executable passes in CI.
- [ ] All unsupported syscall numbers remain ENOSYS; no aliases to unrelated canonical operations.
- [ ] Current-task GETPID returns that task's kernel-owned PID (not a constant).
- [ ] EXIT/EXIT_GROUP tear down the task and address space; WAIT reaps a real exited child.
- [ ] User pointers are checked against the caller's address space.
- [ ] PID 1 can read a known initramfs file through VFS using the real user ABI.
- [ ] One statically linked Linux x86-64 CLI test binary reaches exit status 0.
- [ ] Six production targets (Live/Installer/Recovery × BIOS/UEFI), Aurora, installer/reboot/installed boot, recovery action and AP-backed SMP pass independent traces.

**Release status: BLOCKED until runtime tests prove the above.**
