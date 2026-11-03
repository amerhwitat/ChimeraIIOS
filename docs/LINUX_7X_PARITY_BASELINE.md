# Linux 7.x parity baseline for Koronos and the live editions

**Reference date:** 2026-11-03  
**Kernel baseline:** Linux 7.3.1 stable (2026-10-30); Linux 7.4-rc1 is mainline, not a stable production baseline.

## Boot and PID 1

Linux extracts the built-in or bootloader-provided CPIO initramfs into rootfs. If rootfs contains `/init`, the kernel executes it as PID 1; that process is responsible for locating/mounting the real root and completing userspace startup. Koronos must implement bounded archive parsing, transactional publication, a real root namespace, and an executable PID 1 supervisor. A module scan or a status string is not equivalent.

## VFS and filesystem semantics

Linux VFS separates:
- mount/superblock objects;
- inode objects and filesystem-specific lookup/create/unlink/rename operations;
- dentry/path lookup and cache lifetime;
- open file objects and process file-descriptor tables;
- file operations such as read, write, seek, flush, mmap and release.

The Koronos native implementation must define equivalent ownership, reference counting, locking, path traversal, mount lifecycle, permissions, error propagation, and backend callbacks before a filesystem can be marked native read/write. ISO-9660/UDF optical media remains read-only; writable block filesystems require persistence, remount and crash-recovery tests.

## Device model, buses and DMA

Linux separates device, bus and driver objects and binds drivers after bus/device discovery. PCI/PCIe BARs are bus resources, not CPU virtual pointers. DMA addresses may differ from CPU physical addresses; IOMMUs or bounce buffers may be involved. Every Koronos driver must use a DMA map/unmap contract, device DMA masks, cache-coherency handling, memory barriers and IOMMU isolation where available. ACPI is the PC firmware path; Device Tree is required on many ARM/RISC-V platforms.

## Networking

Linux networking includes device queues, interrupt moderation/NAPI polling, packet processing, socket APIs, neighbour discovery, route/FIB state, policy routing, firewall hooks and userspace control through netlink. A routing tool package is not a Koronos network stack. Koronos still needs NIC drivers, DMA-safe RX/TX rings, packet buffers, IPv4/IPv6, TCP/UDP/ICMP, sockets, route updates, neighbour caches, firewalling and conformance tests.

## CPU and ABI dispatch

CISC/RISC labels do not select a safe executable by themselves. The boot path must validate ELF class, machine, ABI, endianness, required CPU features and firmware mode before loading an image. x86 uses CPUID/APIC/IDT; AArch64 needs EL transitions, system-register discovery and GIC; RISC-V needs privilege-mode/CSR handling, SBI, PLIC/AIA and Sv39/Sv48 page-table setup. Per-CPU interrupt stacks, timers, scheduler contexts, TLB shootdowns and DMA/cache rules are architecture-specific.

## Current implementation boundary

- Canonical Koronos ISO boot pipeline: x86_64 only.
- AArch64/RV64: source/entry scaffolding only; no accepted native EFI/ELF boot.
- CPIO: module scanning/classification exists; transactional root VFS publication is not integrated.
- Native Koronos VFS, mount namespaces, process-owned FDs and general-purpose filesystem backends: not accepted.
- Native Koronos networking/socket/routing stack: not accepted.
- DMA/IOMMU-safe general device driver API and full per-architecture SMP: not accepted.
- Linux live edition: these services are supplied by its bundled Linux kernel and userspace packages; this must not be reported as native Koronos parity.

## Upstream references

- [Linux 7.x release archive](https://www.kernel.org/pub/linux/kernel/v7.x/)
- [Current Linux kernel release page](https://www.kernel.org/)
- [Linux initramfs/rootfs documentation](https://docs.kernel.org/7.2/filesystems/ramfs-rootfs-initramfs.html)
- [Linux VFS overview](https://docs.kernel.org/filesystems/vfs.html)
- [Linux driver model](https://docs.kernel.org/driver-api/driver-model/driver.html)
- [Linux DMA API guide](https://docs.kernel.org/core-api/dma-api-howto.html)
- [Linux NAPI networking documentation](https://docs.kernel.org/networking/napi.html)
