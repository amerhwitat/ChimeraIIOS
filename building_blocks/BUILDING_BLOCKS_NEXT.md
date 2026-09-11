# Building Blocks — Next Layer

The building-block layer now has explicit contract tests and CI wiring. The next production-facing work is target-specific rather than pretending that portable contracts are already hardware implementations.

## Targets

- Koronos: exception/syscall entry, per-CPU scheduling, capability tables and zero-copy IPC.
- Mobile Microkernel: AArch64 exception/MMU/context-switch assembly and RISC-V64 trap/context boundaries.
- Memory: page allocator, virtual-memory mappings, IOMMU and cache/TLB services.
- Spotnik: socket/service boundary, packet rings and zero-copy network paths.
- Boot: Spit Fire/Jasper firmware handoff and image construction.
- Nucleus/Hive: persistence and transaction/service interfaces.
- Aurora: display/input compositor service boundary.
- CEF: foreign ISA emulation/translation outside the privileged core.

Each target must have an executable test or a clearly marked hardware-validation requirement before being described as production-ready.
