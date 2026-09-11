# Mobile Power and Thermal Management

Power management is a first-class mobile-kernel concern but remains policy-driven.

## States

- Active: normal execution.
- Idle: CPU waits for work using architecture-specific low-power instructions.
- Suspend: coordinated device and CPU suspend/resume.
- Hibernate: optional platform-supported deeper state.

## Thermal coordination

The kernel exposes thermal state to scheduling and platform services. A scheduler may reduce placement pressure on thermally constrained CPUs; frequency/voltage control remains delegated to firmware or platform power drivers.

## Battery-aware operation

Background work should use batching, timer coalescing and efficient CPU placement. The kernel must not assume a fixed battery chemistry, charger or power-management IC.
