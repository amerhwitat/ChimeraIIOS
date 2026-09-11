# RISC-V 64 Mobile Architecture

Secondary architecture target for the Mobile Microkernel.

The port isolates privileged trap handling, timer/IPI support, Sv39/Sv48 address-space primitives, context switching, cache/fence operations and platform power-management hooks behind the same mobile kernel interfaces used by AArch64.

Vendor extensions must be discovered explicitly and must not be required by the portable kernel core.
