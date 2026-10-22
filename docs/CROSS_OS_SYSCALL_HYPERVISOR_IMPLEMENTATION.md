# Cross-OS syscall, API, interrupt, and hypervisor implementation status

## Scope and compatibility rule

ChimeraIIOS and OctavianOS aim to host applications through native APIs, compatibility shims, emulation, or virtual machines. Windows NT, Linux, BSD/Unix, and Darwin/macOS are distinct ABIs; they cannot safely be implemented as one syscall-number table. A syscall number or interrupt vector being recognized is not evidence that the operation is implemented. Unsupported calls must return a defined error and must not report false success.

## Current kernel facts observed in source

- The native syscall dispatcher currently implements scheduler yield and timer ticks; GETPID is a placeholder returning PID 1. EXIT/EXIT_GROUP acknowledge the operation but do not perform process teardown.
- READ, WRITE, MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, and ARCH_PRCTL are declared but return ENOSYS in the dispatcher.
- The x86-64 IDT has 256 generated entries, but the current common assembly path must be reviewed and tested for hardware exception error-code frames, stack alignment, register preservation, interrupt-controller EOI, and safe nesting before production claims.
- The current IDT gates are DPL0; the compatibility identities for int 0x80, int 0x2e, and int 0x21 do not establish a working ring-3 Linux, Windows, or DOS syscall entry.
- The compatibility registry already distinguishes metadata/catalog entries from linked implementations. Preserve this fail-closed policy.

## Implementation layers required

1. **Safe common syscall boundary:** validate user pointers and lengths; copy data through fault-safe routines; validate syscall origin, privilege level, and ABI; define errno/status translation; audit integer overflow, handle ownership, cancellation, and process lifetime.
2. **POSIX/Linux/BSD/Darwin:** process/thread lifecycle, file descriptors and VFS, VM mappings/protection, signals, clocks/timers, polling/kqueue/epoll, sockets, credentials, IPC, synchronization, and architecture-specific entry/return paths. Linux, BSD, and Darwin syscall tables and errno conventions remain separate.
3. **Windows:** Win32 user-mode APIs and NT native calls require distinct layers. Handle/object manager, process/thread objects, virtual memory, I/O manager, synchronization, completion ports, registry/configuration, security tokens, PE loader, and subsystem APIs must be implemented and tested; merely recognizing int 0x2e is not an NT syscall implementation.
4. **Mach/Darwin:** Mach traps, ports, VM and task operations are separate from POSIX calls. AppKit/Foundation and Objective-C runtime compatibility are userspace/runtime work, not kernel syscalls.
5. **Interrupts and exceptions:** complete per-CPU IDT/TSS and privilege transitions; architecturally correct error-code frames; PIC/APIC/IOAPIC routing and EOI; timer and IPI handlers; fault containment; syscall entry/return; SMP-safe counters/locks; and tests that inject each supported exception/IRQ. Do not give applications raw hardware IRQ ownership.
6. **Drivers and storage:** user/kernel buffer validation, PCI BAR mapping, DMA mapping and ownership, IOMMU policy where available, virtio queues, block I/O completion/error paths, VFS mounts, and durable filesystem sync must be real before dependent syscalls are marked implemented.

## Hypervisor support

The machine-readable registry `compat/hypervisor-backend-registry.json` inventories open-source VMMs and hypervisors, host requirements, licenses, and honest integration status. QEMU TCG is software emulation, not hardware virtualization. KVM is Linux-host-specific. Xen, bhyve, VirtualBox base, Firecracker, Cloud Hypervisor, crosvm, ACRN, Jailhouse, Bao, Hafnium, OpenBSD vmm/vmd, and NetBSD NVMM require backend-specific adapters and acceptance tests before they can be called integrated.

## Required acceptance evidence

- A generated per-OS/per-architecture syscall matrix with implemented, partial, unsupported, and not-tested states, linked implementation symbols, and tests.
- Unit tests for argument validation and error translation; user-mode integration tests for each implemented syscall family; negative tests for unknown/unimplemented numbers.
- BIOS/UEFI target matrix for Live, Installer, Recovery; production initramfs only; user-originated CPL3 syscall acknowledgement and PID-bound readiness only after required service health checks.
- Interrupt tests per exception/IRQ class and per-CPU tests; storage I/O, filesystem persistence across cold reboot, and Aurora/session handoff.
- Hypervisor backend acceptance results for each supported host/guest combination. Package detection or documentation alone never counts as a passing test.

## Release posture

This registry and roadmap do not mean every Windows/Linux/BSD/Unix/macOS syscall, subroutine, interrupt, optional feature, or hypervisor has been implemented. Those interfaces are large, versioned and architecture-specific. Keep unimplemented paths explicit and keep release artifacts blocked until the relevant executable acceptance tests pass.
