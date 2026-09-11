# Mobile Microkernel — Next Implementation

## AArch64

Implement exception-vector entry, EL transitions, context save/restore, generic timer and GICv3 abstraction behind the HAL. Keep device-specific code outside the portable scheduler and IPC contracts.

## RISC-V64

Implement trap-vector entry, privilege transitions, timer/IPI abstraction and context save/restore. Map platform-specific interrupt-controller behavior into the same service contract as AArch64.

## Memory and power

Add MMU/page-table services, DMA/IOMMU ownership, cache maintenance and suspend/resume state machines. Power sequencing must be supplied by the target SoC firmware contract; portable code should not assume a particular phone chipset.

## Security

Keep capabilities as the authority boundary for device, memory, IPC and network services. Verified boot establishes provenance; runtime policy remains separate from the boot verifier.
