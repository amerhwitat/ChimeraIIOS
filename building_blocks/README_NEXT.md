# Next implementation tranche

This tranche converts the architecture roadmap into testable boundaries without conflating portable prototypes with a bootable production OS.

The repository now has contract-level tests for boot, memory/DMA, scheduling, capability IPC, RegisterN runtime and mobile HAL concepts, plus a GitHub Actions build/test workflow. The following hardware-facing work remains explicitly target-specific: exception vectors, MMU activation, interrupt controllers, context switching, SoC power sequencing, IOMMU programming and boot-image validation.

The implementation order remains: Koronos → Mobile HAL/assembly → memory/DMA → Spotnik → boot/image → Nucleus/Hive → Aurora/CEF → integration tests.
