# RegisterN: Chimera II N-bit CPU register and FPU architecture proposal

Status: architectural proposal / reference-model target; NOT implemented as a complete CPU. Do not label these registers hardware-supported until execution tests, assembler/disassembler tests, ABI tests and boot tests pass.

## Register classes

N is an implementation parameter. The experimental v0.1 interpreter supports N ∈ {32, 64, 128}; its instruction word remains 32 bits, independent of register width. Do not call an 8192-bit CPU implemented just because a research framework uses that label.

| Class | Proposed names | Width | Count | Purpose |
|---|---|---:|---:|---|
| Integer GPR | R0–R15 | N bits | 16 | R0 constant zero; R1 stack pointer; R2 link/return; R3 global pointer; R4 thread pointer; R5–R15 general/ABI-defined |
| Program counter | PC | N bits | 1 | Next instruction address; alignment and address-width rules require ABI ratification |
| Status | FLAGSN | N bits | 1 | Z, N, C, V plus defined exception/interrupt status; reserved bits read as zero |
| Stack/frame | SP, FP | N bits each | aliases | ABI aliases to R1 and R5 unless revised |
| Control/status | C0–C31 | N bits | 32 | Privilege, trap vector, exception cause, return PC, interrupt masks, page-table root, memory attributes and counters; access permissions required |
| Floating point | F0–F31 | N bits storage each | 32 | Scalar formats and packed vector views; storage width does not determine IEEE format |
| FP control/status | FCSR | N bits | 1 | Rounding mode, accrued IEEE exception flags, trap enables and subnormal policy |
| Vector | V0–V31 | N bits baseline | 32 | Baseline vector length N; scalable vectors require separate encoding and context-save rules |
| Predicate/mask | P0–P15 | implementation-defined | 16 | Vector lane masks; inactive-lane and fault policy must be specified |
| Debug/perf | D0–D15 | N bits | 16 | Breakpoints, watchpoints, retired-instruction and cycle counters; privileged access |

F0–F31 and V0–V31 are proposed architectural views, not necessarily separate physical storage. An implementation must define aliasing, context-switch save format and dirty-state tracking.

## FPU semantics required before conformance

- Baseline scalar formats: IEEE 754 binary32 and binary64. Binary16, bfloat16, decimal, complex and extended precision are optional extensions, not implied by N.
- Specify signed zero, infinities, NaNs, subnormals, fused multiply-add, signaling NaNs, comparisons and conversion edge cases.
- Rounding modes: nearest ties-to-even, toward zero, toward positive infinity, toward negative infinity. Any additional mode needs an allocated encoding.
- Sticky exception flags: invalid, divide-by-zero, overflow, underflow, inexact. Define trapping versus flag-only behavior.
- Vector operations must define lane order, endian interaction, saturation versus wraparound, masked-off lane behavior and precise exceptions.
- Reserve encodings before counting an instruction as decoded or executed. Software emulation is not proof of physical FPU support.

## Trap and privilege model

Define User, Supervisor and Machine modes before OS use. Every trap records cause, faulting PC, privilege origin and relevant address. Return instructions restore prior privilege and interrupt-enable state atomically. Specify synchronous exception priority, interrupt priority, nested traps, double-fault behavior and reset state. The v0.1 single-mode interpreter does not meet these requirements.

## Memory model and ABI

- Specify virtual-address translation, permissions, atomic ordering and MMIO ordering.
- Define load/store endianness, alignment, misaligned-access behavior, atomic operations, fences and instruction-cache synchronization.
- Define ELF or another executable format, relocations, calling convention, syscall ABI, exception unwinding, TLS, dynamic linking and context-switch save format.
- A boot ROM, firmware handoff structure, device tree/ACPI equivalent, timer and interrupt-controller contract are prerequisites to a bootable QEMU target.

## Comparison boundary

“Ultra 9” is an Intel Core Ultra product family, not a single register architecture specification. x86-64 architectural state (GPRs, RIP/RFLAGS, XMM/YMM/ZMM, opmask, x87, control/debug registers) is not interchangeable with this proposed RegisterN model. A vendor comparison table must cite the exact processor generation and Intel Software Developer's Manual.

## Acceptance gates

1. Freeze encodings and ABI.
2. Unit-test each register class, flags, NaN/rounding/exception semantics and N-bit wraparound.
3. Assemble/disassemble round-trip every legal encoding and reject reserved encodings.
4. Differential-test floating point against a trusted software reference.
5. Test privilege/traps, MMU, interrupts and context switching.
6. Boot a minimal test kernel and exercise syscalls, timer interrupts and filesystem I/O.
7. Keep native N-bit disabled in the hypervisor registry until these gates pass.
