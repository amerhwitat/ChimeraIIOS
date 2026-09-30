# Native Chimera II OOP, Parallelism, Multithreading and Multitasking

## Object model

Kernel subsystems use freestanding C++ interfaces where useful: `Object` provides intrusive reference counting; `Runnable`, `ServiceObject`, and `DeviceObject` define explicit lifecycle contracts. RTTI and exceptions remain disabled for the kernel, so ownership and failure paths stay deterministic.

## Multitasking

Kore services, drivers and kernel work are represented as independently schedulable tasks. The scheduler maintains explicit task state, priority, CPU assignment, affinity, run counters and tick accounting.

## Multithreading / SMP

Scheduler state is protected by a kernel spinlock and current-task state is maintained per logical CPU. Affinity is a 64-bit mask and the scheduler exposes a multi-CPU dispatch surface. AP startup/interrupt code can invoke per-CPU dispatch concurrently without sharing a single global current-task slot.

`chimera_sched_run_parallel()` is the common dispatch API. It is safe on a single CPU and becomes genuinely concurrent when invoked by active SMP cores.

## Parallel work

Independent work should be partitioned into tasks/chunks and submitted to the scheduler rather than manually sharing mutable state. Future work-stealing and lock-free queues can replace the initial bounded queue without changing the public task API.

## Design constraints

- No C++ exceptions in the kernel.
- No RTTI in the kernel.
- Explicit ownership for heap objects.
- Bounded kernel queues until dynamic allocators are proven safe.
- CPU affinity is optional; zero means scheduler-selected placement.
- Parallel execution is capability-dependent: a UP machine remains deterministic and does not pretend to execute concurrently.
- Driver and service code should expose lifecycle objects instead of global singleton state where practical.
