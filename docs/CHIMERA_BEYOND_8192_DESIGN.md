# Chimera II OS — Beyond-8192-Bit Architecture Design

Status: Design specification
Date: 2026-09-29

## Intent

Extend the Chimera II research execution model beyond the current 8192-bit profile without pretending that commodity x86-64 or ARM64 hardware has a native >64-bit general-purpose ISA. Desktop, Koronos microkernel, and mobile edition must share one logical N-bit model while selecting an implementation backend appropriate to the underlying CPU.

## Core principle

Separate **logical width** from **physical ISA width**.

A Chimera N-bit value is an ordered vector of 64-bit limbs plus metadata. A 16384-bit value therefore occupies 256 limbs, while a 65536-bit value occupies 1024 limbs. The same representation can execute on x86-64, ARM64, or a future native wide/vector backend.

Addresses, page-table indices, capability handles, ABI pointers, and firmware pointers remain architecture-native (currently 64-bit on the supported desktop path). N-bit arithmetic does not silently widen memory addressing.

## Width model

Research profiles are powers of two and may exceed 8192:

`128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576`

The runtime also supports arbitrary positive widths aligned to the selected limb size through a descriptor, subject to memory and scheduler limits. The profile list is a set of tested/recommended widths, not an architectural maximum.

## Logical instruction families

The N-bit layer exposes width-independent operations:

- ADD/SUB
- MUL
- shifts/rotates
- bitwise AND/OR/XOR/NOT
- comparisons and predicates
- wide integer division/modulo where enabled
- modular exponentiation
- population count / leading-zero count
- vectorized lane operations
- tensor contraction descriptors
- serialization/deserialization
- deterministic reduction

Operations are dispatched through a backend interface. The initial backend is portable limb arithmetic; optimized backends may use x86-64, ARM64, SIMD, GPU, or a future native-wide ISA.

## Microkernel boundary

Koronos must not place giant arbitrary-width arithmetic inside privileged scheduling paths. The microkernel owns:

- capability and endpoint IPC
- scheduling and synchronization
- timers/APC/DPC
- address-space and memory protection primitives
- N-bit buffer descriptors and rights checks

Wide arithmetic services execute as capability-controlled kernel services or user-space servers. A syscall submits an N-bit operation descriptor and receives a capability-protected result buffer or completion event.

## Mixed-width IPC

Processes may run at different logical widths simultaneously. IPC never depends on the sender's register width.

The canonical message representation is:

`CHMNBIT1 header + width + signedness + limb_count + payload + optional predicate/tensor descriptors`

The receiver may:

1. consume at native logical width;
2. narrow with an explicit checked conversion;
3. widen with zero/sign extension;
4. request a service backend to transform the value.

No process is required to run in the same N-bit mode as another process.

## Desktop

Aurora/Desktop exposes the active N-bit execution profile and allows switching the profile for new processes and compatible services. Existing processes retain their declared execution contract unless explicitly migrated.

The desktop hardware profiler chooses an implementation backend using CPU features, SIMD capabilities, GPU availability, RAM, and thermal/power policy. Native 64-bit hardware therefore runs a >8192-bit workload as a software/vectorized wide operation rather than as a fictional native instruction set.

## Mobile

The mobile edition uses exactly the same CHMNBIT1 serialization and service ABI. ARM64 devices use the portable limb backend plus ARM64/SIMD acceleration where available. Device-specific boot artifacts remain separate from the common N-bit runtime.

The flash tool must never infer or manufacture a hardware capability from a requested N-bit profile. Device manifests declare supported execution profiles and the installer/runtime selects only profiles supported by the detected device and software backend.

## Compatibility

Legacy 8/16/32/64-bit applications remain isolated behind the existing compatibility layer. A legacy process can communicate with a 16384-bit process through CHMNBIT1 IPC without changing its own ABI.

## Memory and scheduling safety

Wide operations are bounded by explicit resource descriptors:

- maximum operand bytes
- maximum result bytes
- CPU time budget
- memory quota
- cancellation token
- priority/inheritance policy

A 1,048,576-bit value is approximately 128 KiB before metadata. The kernel must not allocate such buffers implicitly from an interrupt or scheduler context.

## Security

- width is validated before allocation;
- integer overflow/truncation is explicit;
- IPC payload lengths are bounds checked;
- capabilities protect result buffers and service endpoints;
- untrusted mobile images cannot request arbitrary privileged wide-mode execution;
- secure boot policy remains independent of logical N-bit width.

## Build and validation gates

The implementation phase will add:

1. a reusable `chimera_nbit` limb library;
2. CHMNBIT1 ABI structures;
3. microkernel buffer/operation descriptors;
4. desktop N-bit service and mode-selection interface;
5. mobile N-bit runtime integration;
6. width profiles through 1048576 bits;
7. arithmetic and serialization tests at 8192, 16384, 32768, 65536 and 1048576 bits;
8. mixed-width IPC tests;
9. GCC and Clang CI coverage;
10. ARM64 cross-build coverage;
11. QEMU boot/runtime smoke tests where practical.

## Non-goals

This design does not claim that current commodity processors execute 16384-bit instructions natively. It provides a portable logical execution model whose implementation may be software, SIMD, GPU-assisted, or future hardware-native.

It also does not change the current 64-bit physical address model or require a >64-bit bootloader ABI.
