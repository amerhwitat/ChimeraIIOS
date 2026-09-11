# Chimera II Building Blocks

This layer consolidates reusable building blocks derived from the Library research archive and public technical references. It is intentionally an implementation layer, not a claim that every referenced technology has been fully implemented.

## Components

- `boot/` — boot-information ABI and verified handoff metadata.
- `memory/` — page-frame ownership, DMA descriptors and bounded packet buffers.
- `kernel/` — scheduler primitives, capability IPC and service contracts.
- `networking/Spotnik/` — zero-copy packet ownership and socket-facing packet flow.
- `runtime/` — wide-register execution boundary and canonical micro-ops.
- `compatibility/` — foreign-architecture translation boundary.
- `database/Nucleus/` — HTAP/neural record interface.
- `database/Hive/` — typed configuration/registry interface.
- `robotics/` — V-Core resource partitions and sensor/actuator data contracts.
- `desktop/Aurora/` — display-compositor service contract.
- `tools/isa/` — instruction metadata validation helpers.

## Provenance

The Library research reports describe the same major layers: bootloader, microkernel, VM/VFS/IPC, networking, HAL, compiler/toolchain, mobile/robotics V-Cores, DMA/zero-copy, and emulator-first validation. These building blocks turn those architectural contracts into small reviewable interfaces rather than copying large third-party source trees.

Public references are recorded in `docs/EXTERNAL_BUILDING_BLOCKS.md`. Third-party source is only imported when its license and provenance permit redistribution. Proprietary, leaked, confidential, or trade-secret code is excluded.
