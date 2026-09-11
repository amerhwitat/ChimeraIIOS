# Universal ISA and CPU Architecture

## Objective

Chimera II OS now separates **native Chimera execution** from **foreign ISA compatibility**. The OS does not flatten every historical CPU encoding into one opcode table. Instead, every supported CPU family is represented by a declarative target descriptor and its instructions are decoded into canonical micro-operations whose operands are normalized into `RegisterN` values.

## Target families

The compatibility registry covers x86-64, AArch64, RISC-V, MIPS64, POWER64, SPARC64, IBM Z/s390x, Motorola 68k, DEC Alpha, PA-RISC, SuperH, Itanium, AVR, Xtensa and WebAssembly, in addition to native C8192/R8192.

This is an extensible registry, not a claim that every instruction of every historical CPU has already been hand-entered. LLVM TableGen is used as a machine-readable import source for architectures it describes. Its documented backends generate instruction, register, scheduling and searchable tables; Chimera consumes neutral metadata and generates its own decoder/translator tables.

## Native encoding

The canonical R8192 base packet remains 64 bits:

```text
bits  0..15  opcode
bits 16..31  destination register
bits 32..47  source A register
bits 48..63  source B register
+ optional 64-bit immediate extension
```

Native instructions operate on `RegisterN<N>` widths. C8192 adds variable packet sizes while preserving the same logical operand model.

## Binary implementation strategy

1. Decode foreign machine bytes using architecture-specific metadata.
2. Produce canonical micro-ops.
3. Map scalar/vector/tensor operands to the smallest compatible `RegisterN<N>` width.
4. Widen to `RegisterN<8192>` only when the operation requires native wide state.
5. Execute natively, translate/JIT, or emulate according to CPU capabilities.
6. Preserve flags, exceptions, memory ordering and privilege semantics in the architecture context.

The LLVM importer is deliberately metadata-driven. This avoids copying vendor source/manual text into Chimera while still allowing large instruction sets to be generated when the corresponding LLVM target description is installed.

## Useful architectural additions

- ISA feature discovery and per-thread ISA profiles
- lazy wide-register state switching
- vector/tensor/crypto execution domains
- atomic and memory-ordering normalization
- deterministic instruction tracing
- binary translation/JIT boundary
- virtualization and VM-exit micro-ops
- performance-counter abstraction
- architecture-specific trap frames
- heterogeneous CPU scheduling
- capability-aware system instructions
