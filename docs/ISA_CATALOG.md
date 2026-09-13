# Chimera II OS RISC/CISC ISA Catalog

Chimera II OS now maintains a canonical machine-readable ISA catalog at `isa/catalog.json`.

## Coverage

| Family | Class | Encoding model | Examples |
|---|---|---|---|
| RISC-V | RISC | 16/32/long optional encodings; RV32I/RV64I | ADD, SUB, ADDI, LW, SW |
| AArch64 | RISC | fixed 32-bit A64 | NOP, RET, ADD, LDR, STR, B |
| ARM32 | RISC | fixed 32-bit A32 | MOV, ADD, LDR, B, BX |
| MIPS32 | RISC | fixed 32-bit | ADD, SUB, LW, SW, JR |
| OpenPOWER | RISC | fixed 32-bit formats | ADD, SUBF, OR, B, BLR |
| SPARC | RISC | fixed 32-bit formats | NOP, ADD, LD, RETL, CALL |
| x86 / Intel 64 / AMD64 | CISC | variable length, prefixes/opcode/ModR/M/SIB/immediate/displacement | NOP, RET, MOV, ADD, JMP |
| Motorola 68000 | CISC | variable word-oriented encodings and effective-address modes | MOVEQ, MOVE, ADD, RTS, BRA |
| IBM System z | CISC | 2/4/6-byte instruction formats | LR, AR, SR, BCR, L |
| VAX | CISC | variable length opcode + operand specifiers | HALT, NOP, RET, RSB, BRB |

## Operand model

Every instruction records operands with a `kind`, and optional operands explicitly use `optional: true` and may provide a default. Operand kinds include registers, memory/effective-address forms, immediate values, signed-relative offsets, masks, displacements, link/absolute flags and fixed operands.

## Binary and hexadecimal forms

Each entry includes a worked binary string and its equivalent hexadecimal representation. These samples encode the exact assembly syntax shown in the same record. They are deliberately kept separate from the general encoding field description so a decoder can distinguish a concrete example from a template.

## Provenance

The catalog records official architecture references plus selected open-source machine-readable references. Intel documents describe IA-32/Intel 64 instruction format and the ModR/M/SIB/immediate structure; AMD documents describe AMD64 variable-length instruction encoding; RISC-V publishes normative opcode maps and instruction listings; OpenPOWER publishes its ISA specification; LLVM's X86 backend provides open-source target descriptions. citeturn0search0turn0search48turn1search1turn2search10turn1search0

The catalog is a factual compatibility database, not a copy of proprietary manuals. Third-party source remains under its original license and the repository stores provenance URLs rather than reproducing large vendor documents.

## Chimera-specific ISAs

The existing C8192/R8192 research ISA remains distinct. Its variable/fixed packet formats, 4096/8192-bit register research model, and Chimera-specific instructions are not presented as external industry-standard encodings. Future Chimera instructions should be added under their own family IDs and provenance.

## Language integration

Adapters exist for C, C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart. `tools/generate_isa_bindings.py` provides deterministic generated adapters for languages where a runtime loader is appropriate. The JSON catalog remains the single source of truth.
