# RegisterN / Chimera Bit Mode

RegisterN is the width-independent logical register model for Chimera II OS. It supersedes the fixed 8192-bit ceiling: a RegisterN value is an arbitrary positive bit width represented as little-endian 64-bit limbs. Widths may be selected at runtime (for example 8192, 16384, 32768, 65536 or larger) without changing the ISA ABI.

## Execution model

- Logical Chimera cores are scheduled independently from physical CPU cores.
- A physical x86-64 CISC, ARM64/RISC or RISC-V host executes canonical Chimera micro-ops through an ISA adapter.
- Host SMT/hardware threads are discovered and exposed as execution lanes; the scheduler may oversubscribe logical Chimera threads.
- NUMA, affinity, vector lanes, accelerator availability and memory locality are scheduler hints.
- RegisterN width is a data-model property, not a claim that the host CPU has native registers of that width.
- Wide arithmetic is limb-parallel and can be accelerated by host SIMD/vector instructions where available.

## Architectural layers

`RegisterN` -> Chimera Bit Mode ISA -> canonical micro-op IR -> host ISA backend (x86-64/ARM64/RISC-V) -> physical CPU.

The same path is used by the emulator, assembler/disassembler, debugger and reverse-engineering tools.
