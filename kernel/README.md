# Koronos low-level kernel
Koronos is the freestanding kernel layer of Chimera II OS.

x86/x86-64 BIOS uses 16-bit real mode, 32-bit protected mode, then long mode. RISC-V uses M/S/U privilege modes. AArch64 uses EL3/EL2/EL1/EL0. R8192/C8192 remain the Chimera research ISA targets.

The hardware boundary is assembly-first. x86 port I/O uses IN/OUT instructions. RISC-V and AArch64 use memory-mapped load/store instructions because those ISAs do not define x86-style port I/O.

The Koronos core is freestanding: no libc, libstdc++, streams, allocation, exceptions, RTTI, or hosted runtime.

ELF64 kernel images and relocatable/shared ELF64 modules are validated by machine type before loading. Relocation, W^X, symbol resolution, and module lifecycle are explicit kernel stages.

## Endianness and execution modes

The canonical policy is in `system/architecture/endianness.json`; freestanding load/store helpers are in `kernel/include/chimera/endianness.h`. x86 real16, protected32 and long64 use little-endian data representation. Mode transitions do not permit the bootloader to assume a different order. ARM32/AArch64 profiles must record the architecture revision and active endian controls; RISC-V targets default to the standard little-endian profile unless a specific supported platform says otherwise; MIPS/PowerPC variants are selected by target ABI; s390x is big-endian. Chimera research targets must declare byte order explicitly.

Boot protocol numeric fields and serialized microkernel IPC use canonical little-endian encoding. In-memory native ABI structures are not wire formats. Emulators preserve guest-visible endianness for memory accesses, instruction fetch, MMIO and exceptions instead of leaking host order. Compatibility loaders validate executable machine and byte-order metadata before decoding. Unsupported profiles are rejected. These helpers and policy are contract-defined; per-backend tests and big-endian-host CI remain acceptance requirements.
