# Koronos low-level kernel
Koronos is the freestanding kernel layer of Chimera II OS.

x86/x86-64 BIOS uses 16-bit real mode, 32-bit protected mode, then long mode. RISC-V uses M/S/U privilege modes. AArch64 uses EL3/EL2/EL1/EL0. R8192/C8192 remain the Chimera research ISA targets.

The hardware boundary is assembly-first. x86 port I/O uses IN/OUT instructions. RISC-V and AArch64 use memory-mapped load/store instructions because those ISAs do not define x86-style port I/O.

The Koronos core is freestanding: no libc, libstdc++, streams, allocation, exceptions, RTTI, or hosted runtime.

ELF64 kernel images and relocatable/shared ELF64 modules are validated by machine type before loading. Relocation, W^X, symbol resolution, and module lifecycle are explicit kernel stages.
