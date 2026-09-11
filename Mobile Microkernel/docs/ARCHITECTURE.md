# Mobile Microkernel Architecture

## Separation

The Mobile Microkernel is a dedicated implementation and build target. It shares stable interfaces and concepts with Koronos but does not depend on the computer kernel's scheduler, device drivers or desktop assumptions.

```text
                 Chimera II OS
                       |
          +------------+------------+
          |                         |
 Computer Edition              Mobile Edition
   Koronos kernel          Mobile Microkernel
          |                         |
 x86-64 / ARM64 / RISC-V     AArch64 / RISC-V64
 desktop/server              battery/thermal/mobile
```

## Privileged core

1. Boot handoff and platform discovery
2. Exception/interrupt dispatch
3. Capability enforcement
4. Address-space and physical-memory primitives
5. IPC and synchronization primitives
6. Preemptive scheduling
7. CPU idle/hotplug coordination
8. Minimal power/thermal hooks

Filesystem policy, networking, neural processing, databases, application frameworks and compatibility environments are userspace services.

## Mobile scheduler

The scheduler models CPU capacity, cluster class, utilization and thermal headroom. Policy can prefer efficiency cores for background work and higher-capacity cores for latency-sensitive workloads without embedding vendor-specific topology in the kernel ABI.

## Trust and isolation

Mobile services communicate through capability-checked endpoints. Driver access is represented as explicit device capabilities. Secure boot, measured boot, verified boot, key storage and rollback protection are platform services whose cryptographic implementation is selected by the target platform.
