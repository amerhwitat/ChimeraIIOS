# Koronos low-level kernel

Koronos is the freestanding kernel layer of Chimera II OS.

x86/x86-64 BIOS uses 16-bit real mode, 32-bit protected mode, then long mode. RISC-V uses M/S/U privilege modes. AArch64 uses EL3/EL2/EL1/EL0. R8192/C8192 remain Chimera research ISA targets.

The hardware boundary is assembly-first. x86 port I/O uses IN/OUT instructions. RISC-V and AArch64 use memory-mapped load/store instructions because those ISAs do not define x86-style port I/O.

The Koronos core is freestanding: no libc, libstdc++, streams, allocation, exceptions, RTTI, or hosted runtime.

ELF64 kernel images and relocatable/shared ELF64 modules are validated by machine type before loading. Relocation, W^X, symbol resolution, and module lifecycle are explicit kernel stages.

## Plug and Play and driver selection

The x86 inventory in kernel/core/device.cpp enumerates PCI configuration space and records vendor/device, class/subclass/programming-interface, revision, BDF and subsystem IDs. The driver manager ranks candidates by bus and ID specificity; no match remains unbound. A metadata match is not a successfully initialized driver. See docs/pnp-driver-discovery.md and system/drivers/catalog.json.

Run python3 tools/drivers/sync_upstream_catalog.py to refresh upstream PCI/USB ID metadata and recursively index relevant Linux, EDK II and Zephyr source paths. The tool indexes sources only and never auto-builds or loads code from the internet.

Discovery is currently limited: PCI configuration mechanism #1 is implemented for x86/x86-64. ACPI/Device Tree, USB host-controller enumeration, PCIe ECAM and mobile SoC buses need their own backends and physical/QEMU validation.

## Endianness and execution modes

The canonical policy is in system/architecture/endianness.json; freestanding load/store helpers are in kernel/include/chimera/endianness.h. x86 real16, protected32 and long64 use little-endian data representation. Mode transitions do not permit the bootloader to assume a different order. ARM32/AArch64 profiles must record architecture revision and active endian controls; RISC-V targets default to standard little-endian unless a supported platform says otherwise; MIPS/PowerPC variants are selected by target ABI; s390x is big-endian. Chimera research targets must declare byte order explicitly.

Boot protocol numeric fields and serialized microkernel IPC use canonical little-endian encoding. In-memory native ABI structures are not wire formats. Emulators preserve guest-visible endianness for memory accesses, instruction fetch, MMIO and exceptions instead of leaking host order. Compatibility loaders validate executable machine and byte-order metadata before decoding. Unsupported profiles are rejected. Per-backend tests and big-endian-host CI remain acceptance requirements.
