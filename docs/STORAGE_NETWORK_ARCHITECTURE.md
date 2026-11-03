# Storage, network and architecture integration boundaries

The Linux 7.x comparison is used as a behavioral reference, not as a claim that
Koronos has imported Linux's VFS, network stack, driver model or scheduler.

## Current Linux live runtime

The ISO rootfs is produced from the Ubuntu runtime image. It now carries
filesystem utilities, network administration/routing tools, development
toolchains and the safe removable-media helper. The Linux kernel supplies the
filesystem and networking drivers actually enabled by its configuration.

## Native Koronos gaps

The kernel tree currently contains CPIO module scanning, ELF admission planning,
CPU feature probing, interrupt/syscall scaffolding and architecture entry
stubs. These do not yet constitute:

- transactional CPIO extraction and root VFS publication;
- mount namespaces, superblocks, inode/dentry caches, page cache, block I/O;
- process-owned file descriptor tables and complete POSIX file operations;
- ext4/XFS/Btrfs/NTFS/FAT/UDF/ISO9660 native backends;
- a native network stack, sockets, route/FIB implementation or NIC DMA queues;
- fully initialized per-architecture interrupt, MMU, syscall and SMP paths.

The filesystem runtime manifest is authoritative for this boundary. A backend
must not be marked read/write until it passes create/read/write/rename/unlink,
permission, remount, crash-recovery and persistent-media tests.

## Device and mount contract

Linux live editions use devtmpfs/udev for /dev, procfs for /proc, sysfs for
/sys, tmpfs for /tmp and udev-triggered media discovery under /media. Optical
ISO-9660/UDF is read-only; removable writable media is allow-listed and mounted
with nosuid,nodev,noexec. No automatic format or repair occurs.

## Architecture dispatch

The canonical ISO currently emits x86_64 only. AArch64 and RV64 source folders are port scaffolding; the integration build can cross-compile
architecture/hardware probe objects when cross toolchains are present, but those objects are
not linked into a kernel and are not bootable targets. Each architecture needs matching
entry/EFI/ELF artifacts, ABI checks, interrupt controller, timers, MMU, DMA
and device enumeration before target selection can be enabled.

CISC/RISC is not a sufficient binary selector: the bootloader must validate
ELF class, machine, ABI, endianness and required CPU features. Hardware feature
discovery must be separated from OS-enabled state (for example AVX requires
OSXSAVE/XCR0). DMA must use map/unmap APIs and account for IOMMU and cache
coherency. PCI/PCIe uses bus enumeration; non-PC ARM/RISC-V platforms require
Device Tree or platform firmware data, while PC systems generally use ACPI.

## Root account

The runtime root account is present but locked by default. Administrative work
uses a separate unprivileged account with explicit sudo authorization. Never
ship a known shared root password.
