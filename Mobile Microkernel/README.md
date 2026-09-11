# Chimera II OS Mobile Microkernel

Dedicated mobile implementation of the Chimera II OS kernel architecture.

## Scope

The Mobile Microkernel is intentionally separate from the computer-oriented Koronos implementation while preserving compatible IPC, capability, memory-bus, ISA and service interfaces.

Primary target: **AArch64 mobile SoCs**. Secondary architecture path: **RISC-V 64**.

The mobile design prioritizes:

- energy-aware scheduling and CPU affinity;
- heterogeneous CPU clusters and latency-sensitive UI workloads;
- suspend/resume and thermal/power coordination;
- capability-based isolation and least-privilege drivers;
- IOMMU/DMA-aware memory services;
- secure/verified boot integration;
- touchscreen, display, GPU, audio, camera, sensors, storage, Wi-Fi, Bluetooth, USB and cellular driver boundaries.

## Directory layout

```text
Mobile Microkernel/
├── arch/                    architecture-specific code
├── boot/                    mobile boot and verified-boot interfaces
├── drivers/                 hardware-facing driver boundaries
├── include/chimera/mobile/ public kernel interfaces
├── src/                     kernel implementation
├── tests/                   host/emulation/unit tests
├── tools/                   mobile build/inspection helpers
└── docs/                    architecture and porting documentation
```

## Design boundary

The mobile kernel owns privileged scheduling, IPC, capabilities, memory-management primitives, interrupts/traps and low-level power coordination. Networking, databases, neural runtimes, VFS policy, compatibility layers and application services remain outside the privileged kernel wherever practical.

This is a research/engineering implementation. Vendor-specific hardware must be integrated through explicit HAL/driver interfaces rather than assumed to be universally available.
