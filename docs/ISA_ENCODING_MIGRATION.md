# Chimera II ISA Encoding Migration Plan

## Objective

Integrate the expanded bit-level opcode metadata into Chimera II without breaking the existing R8192 fetch/decode/execute contract.

## Current baseline

The native ISA occupies `0x0001..0x011C` (284 instructions). The emulator has moved from the earlier 8-bit native-opcode assumption to a 16-bit native opcode model.

## Integration layers

### Layer 1 — Semantic registry

`src/isa/chimera_isa.cpp` and the existing R8192 metadata catalog define instruction identity, privilege, execution family, and dispatch behavior.

### Layer 2 — Encoding registry

`tools/isa/isa_opcodes_expanded_with_encodings.csv` is reserved for the expanded encoding-aware metadata. It adds encoding templates, opcode bit placement, immediate width, ModR/M-like indicators, and illustrative binary vectors.

### Layer 3 — Decoder generator

A future generator should consume the encoding registry and emit constexpr C++ descriptors and assembler/disassembler tables. Generated code must never silently change opcode assignments.

### Layer 4 — Test vectors

Every canonical encoding eventually needs positive and negative vectors covering:

- encode → decode identity;
- opcode identity;
- operand identity;
- immediate identity;
- instruction length;
- reserved bits;
- privilege;
- malformed encodings.

## Important compatibility rule

The existing emulator uses a fixed 16-byte host packet. Logical instruction encodings of 32, 64, 96, 128 bits or other sizes must be normalized to that packet or handled by an explicit extension mechanism. Do not infer that an illustrative hexadecimal example changes the host packet ABI.

## Partial-source handling

The expanded CSV supplied in the project discussion terminates part-way through the `RSAMOD` row. Missing rows must not be fabricated. The integration therefore records the encoding schema and supplied verified rows while preserving the complete existing 284-opcode semantic catalog. The remaining encoding rows should be imported when the complete source artifact is supplied.

## Promotion path to canonical encoding

1. Complete the expanded CSV.
2. Validate all 284 opcode mappings against the semantic registry.
3. Freeze instruction lengths and field positions.
4. Define canonical endianness and reserved-bit rules.
5. Generate assembler/disassembler descriptors.
6. Add round-trip tests for every instruction.
7. Add compatibility tests against the existing executor.
8. Publish a versioned ISA encoding specification.
9. Only then mark the encoding layer `canonical`.
