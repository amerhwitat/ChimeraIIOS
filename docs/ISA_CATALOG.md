# Chimera II OS RISC/CISC ISA Catalog

Chimera II OS maintains two complementary machine-readable ISA resources:

- `isa/catalog.json` — the richer structured instruction catalog with worked binary/hex samples, operand objects and architecture-family metadata.
- `ISA.csv` — the portable tabular export requested for build, analysis and spreadsheet tooling. It records architecture, RISC/CISC class, mnemonic, syntax, binary encoding/template, hexadecimal encoding/template, operands, optional operands and notes.

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

## Operand and encoding model

Each CSV row identifies the operand fields and optional operands. An ISA instruction does not always have one universal hexadecimal value: register numbers, immediates, displacements, ModRM/SIB fields, branch offsets and addressing modes change the encoded bits. Therefore `ISA.csv` uses an exact literal encoding for fixed instructions and an explicit template/expression for variable fields.

The supplied architecture material explains that an instruction contains an opcode and operands, and that machine language is the CPU's binary instruction format. fileciteturn90file0L38-L48 It also describes RISC fixed-length versus CISC variable-length instruction formats. fileciteturn90file0L125-L147 The second supplied lecture identifies operation repertoire, data types, instruction format, registers and addressing as fundamental ISA design issues. fileciteturn90file1L5-L30

## Current authoritative references used by the catalog

- Intel's current Intel 64/IA-32 Software Developer Manuals include the full instruction-set reference and instruction-format descriptions. citeturn0search0turn0search5
- RISC-V International's current ratified ISA library provides unprivileged and privileged specifications; the unprivileged specification defines base integer ISAs plus optional extensions and instruction-length encoding. citeturn0search2turn0search3turn0search4
- OpenPOWER publishes the Power ISA specification, including user, virtual-environment and operating-environment architecture books. citeturn1search0
- Oracle's SPARC documentation provides SPARC-V9 instruction-set mappings and instruction categories. citeturn1search1turn1search7
- Arm's A64 architecture material documents encoded fields for instructions such as LDR and explains their structured field layout. citeturn1search13

## Validation and ISO integration

`tools/isa/validate-isa.py` validates the CSV schema and architecture coverage. The ISO preparation script copies `ISA.csv` into `/src/ISA.csv`, and the ISO build invokes the validator before mastering the ISO. GitHub Actions also validates the catalog before the Docker ISO build.

## Completeness policy

The phrase “all CISC and RISC processors” cannot be represented honestly as one finite instruction list without defining a revision, extension set and vendor scope. Processor families have revisions, optional extensions, privileged instructions, vector/crypto extensions, aliases and implementation-specific encodings. Chimera therefore maintains a cross-architecture base catalog and preserves the richer JSON catalog as the extensible source. Architecture-specific decoder/encoder tables should be added from each architecture's normative manual when that ISA is enabled for native execution.

## Chimera-specific ISA

The C8192/R8192 research ISA remains separate from external industry-standard ISA definitions. Chimera-specific encodings should be registered under a dedicated family ID and must not be represented as Intel/AMD/Arm/RISC-V/MIPS/Power/SPARC encodings.
