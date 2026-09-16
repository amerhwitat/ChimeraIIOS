# Chimera II ISA Registry and Instruction Encoding Design

**Goal:** Build a provenance-first, machine-readable ISA registry for Chimera II OS covering its native ISA plus major RISC/CISC CPU families, with instruction operands, encoding fields, opcode bit patterns, canonical binary examples, semantics, privilege, and source provenance.

## Scope

The registry distinguishes three layers:

1. **ISA families** — x86/x86-64, AArch64/A32, RISC-V, MIPS32, Power ISA, SPARC V9, SuperH-4, LoongArch64, Alpha, PA-RISC, Xtensa, AVR, 68000, VAX, IBM z/Architecture, 8051, Z80, 6502, and the Chimera C8192/R8192 native research ISA.
2. **Encoding templates** — instruction length, byte order, opcode/value-mask, field layout, prefixes and extension selectors.
3. **Instruction records** — mnemonic, operand kinds, semantic inputs/outputs, flags, memory/control-flow effects, privilege, exact encoding pattern and a canonical all-zero-register/immediate example where the architecture permits one.

## Accuracy boundary

A single binary value does not exist for many instructions because register/immediate/displacement fields are operands. Therefore every record stores both the fixed opcode/pattern and a canonical concrete encoding when one can be represented without inventing operands. x86 records use opcode bytes plus ModR/M or immediate templates rather than pretending one byte encodes every form. RISC-V records store opcode/funct fields and canonical 32-bit examples. AArch64 records store the fixed 32-bit mask/value and field names.

The registry is not a verbatim copy of proprietary manuals. It stores normalized metadata and short encoding descriptors with citations to authoritative architecture specifications.

## Chimera-native ISA

Chimera C8192/R8192 is treated as a research ISA owned by this project. Its existing conceptual operations (ADD, MUL, TCONTRACT, MODEXP, NETSEND and related register/memory/network operations) are explicitly marked `custom/chimera-native`, not presented as industry-standard encodings. Native binary values are assigned from a reserved Chimera opcode namespace and documented as project-defined.

## Database

`isa/isa_database.json` is the canonical JSON database. `isa/isa_database.sql` mirrors the normalized tables for SQLite import. `isa/instructions.json` is the instruction-focused export used by tooling. `isa/world_architectures.json` remains the top-level architecture index and points to the instruction database.

## Validation

The validator must reject duplicate `(architecture, mnemonic, form_id)` records, malformed binary strings, impossible bit widths, missing operands/encoding/semantics, and Chimera records lacking `custom` provenance. Tests cover schema shape, uniqueness, binary lengths, canonical encodings, and cross-file architecture references.
