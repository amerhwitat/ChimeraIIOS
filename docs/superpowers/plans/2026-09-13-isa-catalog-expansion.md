# Chimera II OS ISA Catalog Expansion

## Goal
Create a provenance-first, machine-readable instruction-set catalog covering representative mainstream RISC and CISC families, their operand structures, instruction-length/encoding templates, and canonical binary/hex examples. Generate language-specific constants/adapters from one canonical catalog rather than duplicating independently maintained tables.

## Scope
- RISC: RISC-V RV32I/RV64I plus common ratified extensions; AArch64/A64; ARM32; MIPS32/64; Power ISA; SPARC.
- CISC / legacy-rich: x86/IA-32/Intel 64/AMD64; Motorola 68000 family; IBM System/390-z/Architecture; VAX/PDP-11 reference families.
- Include ISA family, endianness, register model, instruction length, operand kinds, optional operands, encoding fields, opcode/mask metadata, and worked binary/hex examples.
- Include exact public-source citations/provenance and clearly distinguish exact encodings from illustrative operand templates.
- Extend Chimera C8192/R8192 as separate native research ISAs; do not conflate them with external ISA encodings.

## Architecture
- `isa/catalog.json` is canonical.
- `isa/schema.json` validates catalog shape.
- `isa/README.md` explains scope, provenance, and encoding conventions.
- `tools/validate_isa_catalog.py` validates required fields, duplicate IDs, binary/hex consistency, and operand metadata.
- `tools/generate_isa_bindings.py` emits deterministic language adapters for C, C++, Rust, Python, Java, C#, Kotlin, Swift, TypeScript and Dart.
- Generated/reference language files live under `isa/<language>/`.
- CI validates the canonical catalog and compiles/syntax-checks all generated adapters.

## Safety / legal boundary
Do not copy proprietary vendor manuals or large upstream source trees. Store factual opcode/encoding data, short instruction names/syntax, and source URLs/provenance. Preserve third-party licenses. Prefer official ISA specifications and permissively licensed/open-source machine-readable references such as LLVM/binutils where suitable.

## Verification
1. Validate JSON/schema and binary/hex round trips.
2. Compile C/C++/Rust and syntax-check Python/TypeScript/Dart/Swift/Java/Kotlin/C# generated files where toolchains are available in CI.
3. Confirm CI workflow success before claiming completion.
