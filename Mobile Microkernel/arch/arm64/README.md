# AArch64 Mobile Architecture

Primary architecture target for the Chimera II OS Mobile Microkernel.

The architecture layer owns exception/interrupt entry, context switching, MMU/page-table primitives, cache maintenance, barriers, timers, CPU idle instructions and platform discovery. SoC-specific drivers remain outside this generic layer.

Initial platform contract:

- AArch64 EL transition into the kernel;
- GIC-compatible interrupt abstraction where available;
- generic timer abstraction;
- MMU and ASID-aware address-space interface;
- WFI/WFE idle hooks;
- PSCI-compatible power-control boundary when firmware exposes it.
