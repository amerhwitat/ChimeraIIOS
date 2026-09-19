# Koronos and Linux 7.2.2 compatibility

This is a compatibility and identification layer, not a copy of Linux. The requested Bootlin recursive endpoint was blocked by robots policy in this environment, so the integration uses the requested source reference plus public kernel.org architecture documentation and independent Linux 7.2.2 release/source references. Linux source remains separately licensed; no Linux source files are copied into Koronos.

## Feature contract

Koronos tracks process/thread lifecycle, scheduling, signals, futexes, RCU, workqueues, timers, virtual memory, page cache, huge pages, swap, slab allocation, VFS/filesystems, block I/O, DMA, device model, PCI, USB, TTY, input, graphics/DRM, sound/media, IPv4/IPv6, TCP/UDP, routing, netfilter, sockets, zero-copy networking, IPC, pipes, epoll, io_uring, syscalls, ELF, modules, namespaces, cgroups, seccomp, LSM, crypto, keyrings, tracing/ftrace/perf/BPF, procfs/sysfs/debugfs, firmware, ACPI, DeviceTree, UEFI, power management, CPU hotplug, virtualization/KVM, kexec, compression, livepatch, fault injection, lockdep, sanitizers, atomics and memory barriers.

The registry distinguishes a compatibility contract from a completed backend. A registered feature can later be backed by native Koronos code, a translator/emulator, or an explicitly unsupported capability.

## Architecture contract

The architecture registry covers x86/x86-64, ARM/ARM64, RISC-V, Power/PowerPC, MIPS, SPARC, s390, SuperH, m68k, PA-RISC, Alpha, ARC, C-SKY, Hexagon, LoongArch, MicroBlaze, Nios II, OpenRISC, Xtensa and User Mode Linux.

Kernel.org architecture documentation separates architecture-specific implementation from common kernel facilities and documents the architecture-specific trees. https://www.kernel.org/doc/html/latest/arch/

## ISA relationship

The attached RISC/CISC material describes RISC load/store/register-oriented designs and CISC designs with richer addressing and variable-length/multi-cycle instructions. It also covers assembler directives, pseudo-instructions and two-pass symbol resolution. The relevant lecture material identifies RISC and CISC families and their addressing/format differences. The material supplied for this task is cited in the project documentation.

Koronos uses the boundary:

Linux architecture backend -> normalized CPU context -> Chimera canonical micro-ops -> R8192/C8192 execution.

This preserves the distinction between external machine encodings and the common kernel execution model.

## Current implementation

linux_compat.hpp/.cpp provide feature and architecture registries plus a runtime compatibility report. The implementation is linked into chimera_machine, so chimera_kernel initializes against the same registry and reports the detected compatibility surface at startup.

A complete Linux binary/runtime compatibility environment still requires concrete ABI personalities, syscall tables, signal frames, futex semantics, VFS adapters, socket ABI, device-driver shims, io_uring semantics, namespaces/cgroups, BPF execution, KVM interfaces and architecture-specific trap/return paths. Those are deliberately not represented as completed merely by registration.
