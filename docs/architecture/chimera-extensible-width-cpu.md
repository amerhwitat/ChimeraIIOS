# Chimera II extensible-width CPU architecture (RegisterN / XN)

**Status:** design specification plus a limited arbitrary-width arithmetic reference interpreter. This is not an implemented infinite-width physical CPU, a full x86 clone, or a bootable privileged machine.

## 1. Width model: no fixed architectural N, finite implementation resources

The architecture defines a width parameter N rather than one fixed maximum architectural width. Each implementation advertises a finite supported-width set and resource limits. The current Python reference model accepts byte-aligned N from 8 through 1,048,576 bits (a practical safety ceiling), so 16,384- and 32,768-bit arithmetic can be tested. It does not implement literally infinite registers: physical storage, execution time, memory, instruction encoding and address translation are finite.

Register width and address width are independent parameters: N (integer register width), VA_BITS (virtual address bits), PA_BITS (physical address bits), INSN_BITS (currently 32 in the prototype), and VECTOR_BITS. An N-bit register does not imply an N-bit pointer, unlimited RAM, or an N-bit instruction.

Unsigned arithmetic wraps modulo 2^N; signed arithmetic uses two's-complement interpretation of the same N-bit bit pattern. Every operation defines overflow, carry, sign and zero behavior. Addresses must be validated against implemented VA/PA width and mapped regions before access; never silently truncate an invalid pointer.

## 2. Intel-inspired system architecture, not x86 binary compatibility

The design borrows system-architecture concepts from the Intel 64 / IA-32 manuals, but it is a new ISA. Similar names do not make encodings, privilege semantics, exception behavior, or binaries compatible with Intel CPUs. Existing Intel register and table structures remain in the x86 compatibility execution engine, not silently redefined as RegisterN.

### Proposed architectural register banks

- Integer: R0..R31, each N bits; R0 reads as zero and ignores writes. ABI candidates: R1=SP, R2=link, R3=global pointer, R4=thread pointer; all ABI assignments need ratification.
- PC and flags: PC width VA_BITS; FLAGSN contains defined Z/N/C/V plus interrupt and exception state. Reserved bits read as zero.
- Control/system: CR0..CR15, N bits, with named architectural fields for mode, paging enable, write protection, translation root, NX policy, compatibility controls and fault configuration. Reset values and write masks are required.
- Descriptor-table registers: GDTR, IDTR, LDTR, TR, each with explicit base/limit/selector or descriptor-cache fields. RegisterN table descriptors are defined by a new versioned format; x86 descriptor bytes must only be parsed by the x86 compatibility engine.
- Segment model: CS, SS, DS, ES, FS, GS logical selectors; optional flat-address mode first. Segment bases/limits and privilege checks are explicit when segmentation is enabled.
- Debug/performance: DR0..DR15 N-bit values with privilege checks, breakpoint type/length and performance counter access controls.
- FPU: F0..F63 with N-bit storage; supported IEEE formats (binary32/64 baseline target) are independent of storage width. FCSR includes rounding mode and sticky invalid/divzero/overflow/underflow/inexact flags. Full x87 stack compatibility is implemented only in the x86 engine.
- Vector/predicate: V0..V63 N-bit baseline storage and P0..P31 lane masks, with separately specified vector length, lane ordering, inactive-lane behavior and exception policy.
- Compatibility state: x86 engine preserves legacy GPRs, RIP/RFLAGS, segment state, x87, MXCSR, XMM/YMM/ZMM, opmask, control/debug/MSR state only to the extent implemented and advertised by its selected CPU model. Never invent support for undocumented model-specific registers.

These counts are a proposed architectural profile and may evolve before ABI freeze; current executable reference tests only integer arithmetic, simple loads/stores, branches and basic software traps.

## 3. Descriptor tables and interrupt architecture

Define the following structures before enabling supervisor mode:

- GDT / LDT: versioned descriptors with base, limit, type, privilege, present, executable/readable/writable and granularity attributes; validate every selector, privilege transition and table bound.
- IDT: vector-indexed interrupt/trap gates with handler address, gate type, target privilege, present bit and optional interrupt-stack selector.
- TSS-equivalent: per-privilege stack pointers, interrupt-stack table, I/O permission policy and task-state version; hardware task switching is not implied.
- IDTR/GDTR bounds: descriptor reads must check table limit, entry size, canonical/implemented address constraints and mapped memory before dereference.
- Interrupt controller: explicit source IDs, masking, priority, pending/in-service state, end-of-interrupt semantics, level/edge trigger and inter-CPU delivery contract.
- Trap frame: saved PC, flags, privilege, stack pointer, vector/cause, error code when defined, and fault address. Trap entry must be atomic from the guest perspective.
- Return-from-interrupt: validate restored PC, stack, privilege and flags before state changes; reject invalid returns with a defined fault/double-fault policy.
- Exceptions: assign stable vectors and priorities for illegal instruction, divide-by-zero, page fault, protection fault, alignment, external interrupt, NMI, double fault and machine check. A vector number alone is not proof that the handler or recovery path is implemented.
- MMU: define canonicality/address-width rules, multi-level page tables, permissions, NX, access/dirty bits, TLB invalidation, ASIDs/PCIDs, huge pages, memory types, DMA/IOMMU interaction and memory-ordering fences.

Do not enable ring/user isolation until privilege transitions, descriptor validation, page permissions and return-from-interrupt have adversarial tests.

## 4. FPU and extended registers

A wide F0 register is storage, not an IEEE 754 number of that width. Arithmetic semantics are selected by operation format. Specify binary16/32/64, optional bfloat16 and any wider software-defined formats individually. Require reference differential tests for rounding ties, signed zero, NaNs, subnormals, fused multiply-add, conversions and all exception flags. Vector/FPU context must be saved and restored on task switches; lazy state switching must avoid cross-process leaks.

## 5. RISC compatibility

Compatibility means a separate, explicit ISA execution profile and ABI—not changing RegisterN instructions into RISC instructions by renaming registers.

- RV32I/RV64I/RV128I: distinct XLEN profiles with independently defined extensions, CSR access, privilege modes and encodings. RV128I must not be claimed unless implemented by a conforming toolchain/reference and tests.
- Other RISC profiles: ARM/AArch64, MIPS, PowerPC, SPARC, s390x and other targets use their own machine/CPU state and guest ABI. Use a validated interpreter/JIT or QEMU TCG for supported targets; do not reuse RegisterN decoder semantics.
- ABI boundary: guest syscalls, ELF relocations, endianness, atomic ordering, MMIO, exceptions and device tree/ACPI/firmware contracts are per target.
- Cross-ISA execution: translation or interpretation can execute supported guest instructions; it does not make host hardware a native CPU for every ISA. KVM is an accelerator for compatible configurations, while TCG provides software emulation for QEMU-supported targets.

## 6. Build plan and acceptance gates

1. Freeze the RegisterN encoding, ABI, memory model and privilege-state transitions.
2. Implement decoder/encoder with illegal-encoding rejection and round-trip tests.
3. Implement flags, integer operations, atomics and fault-precise memory semantics for 32, 64, 128, 8192, 16384 and 32768-bit profiles.
4. Implement and fuzz descriptor-table parsing, privilege transitions, interrupt entry/return and double-fault behavior.
5. Implement MMU/TLB, timers, interrupt controller and deterministic device model.
6. Implement FPU/vector operations and differential-test against trusted reference libraries.
7. Add assemblers, linkers, debugger state, ELF ABI and context switching.
8. Boot a minimal kernel per implementation profile; verify timer interrupts, syscalls, memory protection and filesystem I/O.
9. Register as executable only the features that pass their gates. Maintain separate documented/encoded/decoded/executed/conformance-tested/boot-tested statuses.

## References

- Intel 64 and IA-32 Architectures Software Developer's Manuals: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
- QEMU system emulation and accelerator model: https://www.qemu.org/docs/master/system/introduction.html
- QEMU emulation target matrix: https://www.qemu.org/docs/master/about/emulation.html
