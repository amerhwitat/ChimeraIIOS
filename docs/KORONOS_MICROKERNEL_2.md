# Koronos Microkernel 2 Architecture

Koronos is extended with an explicit architecture-independent service layer. Scheduling, IPC, memory, interrupts, capabilities, timers, tracing, VFS, networking, databases and virtualization are modeled as independently testable services.

## CPU state

Each thread owns a compact architecture context. Wide `RegisterN<8192>` state is lazy: it is materialized only when a thread executes a wide/vector/tensor instruction. This prevents ordinary 64-bit workloads from paying an 8192-bit context-switch cost.

## IPC

Database and device services use shared-memory, zero-copy rings where safe. Capability checks occur before mapping shared memory or invoking privileged services.

## Scheduling

The architecture layer exposes CPU feature vectors to the scheduler. A task can declare required features such as vector, crypto, tensor, atomics or native Chimera execution. The scheduler may migrate the task only when the destination CPU satisfies the declared profile.

## Isolation

Foreign ISA execution belongs in userspace compatibility/emulation services where possible. Kernel code consumes only normalized traps, page faults, interrupts, IPC requests and capability operations.

## Database services

Databases remain outside the kernel. The new Database service descriptor provides the stable Koronos boundary for Nucleus, Hive and application databases without linking MariaDB, PostgreSQL or NoSQL engines into the microkernel itself.
