# Chimera II ISA: RISC/CISC and Assembler Integration

**Source basis:** Hakim Weatherspoon, *RISC, CISC, and Assemblers*, CS 3410, Spring 2012, Cornell University, pages 4–30.

This document records how the source's instructional concepts are mapped into the project-defined Chimera ISA without treating the source as a specification for Chimera encodings.

## 1. ISA design profiles

Chimera exposes two native execution profiles:

- **R8192 — RISC profile:** regular 64-bit instructions, register-oriented operands, explicit load/store memory operations, and predictable formats suitable for pipelining.
- **C8192 — CISC profile:** explicit 64–4096-bit packets, denser encodings, richer operation forms, and a micro-op lowering boundary for complex operations.

The source describes RISC as emphasizing regularity, simplicity, and optimization of common cases, while CISC emphasizes richer encodings, code density, legacy/compatibility, and microcode. Those principles are used here as architectural design guidance.

## 2. Instruction formats

The source contrasts fixed 32-bit MIPS formats with variable-length x86 encodings and describes instruction operands, immediates, branches, memory operations, and control flow. Chimera therefore makes its format choice explicit:

| Profile | Base form | Extended form | Purpose |
|---|---|---|---|
| R8192 | fixed 64-bit word | explicit immediate/relocation extension | predictable decode |
| C8192 | 64-bit base packet | explicit 128/256/512/1024/2048/4096-bit packet | density and complex operations |

Chimera does **not** reuse MIPS, ARM, x86, or other external binary encodings as native encodings.

## 3. Assembler pipeline

The source describes assembly as a combination of instructions, pseudo-instructions, and data/layout directives, producing an object/executable representation. Chimera adopts the following deterministic pipeline:

1. Parse source text.
2. Process sections and layout directives.
3. First pass: assign addresses and build the symbol table.
4. Second pass: encode instructions/data and resolve symbols.
5. Emit relocation information where an address cannot be finalized locally.
6. Produce an object, boot image, or OS image as requested by the toolchain.

The two-pass rule is important for forward labels and branch/address references.

## 4. Sections and directives

The assembler supports the conceptual separation described in the source:

- `.text` — executable instructions
- `.rodata` — read-only constants/strings
- `.data` — initialized writable data
- `.bss` — zero-initialized/uninitialized storage

Layout/data directives include `.byte`, `.word`, `.dword`, `.qword`, `.align`, `.org`, `.global`, `.extern`, and `.section`.

## 5. Pseudo-instructions

Pseudo-instructions are assembler conveniences rather than new hardware operations. The initial Chimera set includes `NOP`, `MOVE`, `LI`, `LA`, `B`, and `BLT` aliases/lowering forms. Their expansion must be deterministic and visible to assembler diagnostics/listing output.

`LI` and `LA` may expand to multiple native instructions when an immediate/address does not fit a single encoding. Relocations remain explicit in the object representation.

## 6. Compatibility layer

External architectures remain separately encoded. A compatibility assembler/translator may lower source ISA instructions into Chimera's canonical micro-op vocabulary:

`ALU`, `SHIFT_ROTATE`, `LOAD`, `STORE`, `BRANCH`, `CALL_RETURN`, `ATOMIC_RMW`, `VECTOR`, `TENSOR`, `CRYPTO`, `DMA`, `NETWORK`, `SYSCALL`, `VMEXIT`, and `FENCE`.

This permits x86, ARM, RISC-V, MIPS, Power, SPARC, 68000, VAX, and related compatibility targets without conflating their published encodings with the project-defined Chimera encoding.

## 7. Calling conventions

The source's final section introduces calling conventions and demonstrates argument, return-value, and return-address register usage. Chimera keeps this boundary separate from the ISA: the assembler preserves register names, symbols, relocations, and call/return instructions, while ABI profiles define argument and return registers.

## 8. Traceability

The source material explicitly covers ISA variations, RISC/CISC complexity, MIPS and ARM formats, assembly instructions, pseudo-instructions, data/layout directives, object-file structure, two-pass assembly, and executable-program staging. These concepts are represented in `isa/spec/chimera_isa.yaml` and this document.

Source-derived concepts are not claims that the 2012 lecture specifies Chimera hardware. Chimera-native widths, packet formats, opcode ranges, and micro-ops remain project-defined.
