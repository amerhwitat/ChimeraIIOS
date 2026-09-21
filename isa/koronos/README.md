# Koronos ISA boundary
This directory connects the existing Chimera R8192/C8192 normalized ISA registry to the physical CPU entry layer.

x86-64 is treated as the CISC boundary: BIOS real16, protected32, long64, and port I/O via IN/OUT.
RISC-V64 and AArch64 are treated as RISC boundaries: privilege modes and MMIO load/store replace x86 port I/O.
The Chimera R8192/C8192 ISA remains a research architecture and is not represented as existing silicon.

The kernel ABI is freestanding and assembly-first. C/C++ may be used as a freestanding implementation language, but hosted C/C++ libraries are deliberately excluded from the hardware boundary.
