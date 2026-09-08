# Chimera II R8192 ISA Encoding Specification

**Status:** Experimental / research architecture
**Version:** 0.1
**Date:** 2026-09-08

## Purpose

This document defines the integration contract for bit-level encoding metadata supplied for the Chimera-R8192 instruction set. The encoding templates are tooling-oriented descriptions used to guide assembler, disassembler, decoder, test-vector, and documentation generation.

They are **not authoritative hardware encodings** unless a future Chimera II ISA revision explicitly promotes them to canonical status.

## Canonical execution packet

The current emulator retains a fixed 16-byte host instruction container. Native decoding uses a little-endian 16-bit opcode followed by three 16-bit operand fields and an optional 64-bit immediate:

```text
bits 15:0    opcode
bits 31:16   rd / destination
bits 47:32   srcA
bits 63:48   srcB
bits 127:64  optional immediate / extension payload
```

The expanded encoding metadata may describe shorter or longer logical instruction encodings. Such encodings must be normalized into the canonical host packet before execution.

## Encoding classes

| Tag | Meaning |
|---|---|
| R | Register / ALU form |
| I | Immediate or address form |
| M | Multi-field / extended immediate form |
| V | Vector or wide-lane form |
| S | System/service form |
| P | Predicate/mask form |
| L | Load/store form |

## Metadata schema

```text
mnemonic;opcode;encoding;operands;privilege;latency;throughput;pipeline_stage;isa_family;notes;source_ref;encoding_template;opcode_bits;imm_size;modrm_like;example_binary
```

### Field rules

- `mnemonic`: unique instruction mnemonic.
- `opcode`: 16-bit native opcode identifier in the current R8192 namespace.
- `encoding`: encoding-class tag.
- `operands`: assembler-visible operand order.
- `privilege`: `user` or `priv`.
- `latency`: architectural scheduling target, not a physical measurement.
- `throughput`: architectural scheduling target, not a physical measurement.
- `pipeline_stage`: intended execution stage/family.
- `isa_family`: native family such as `R8192`, `SPOTNIK`, or `HYBRID`.
- `notes`: semantic description.
- `source_ref`: provenance label.
- `encoding_template`: MSB-to-LSB bitfield description.
- `opcode_bits`: opcode value placed into the template.
- `imm_size`: immediate field width in bits.
- `modrm_like`: whether a ModR/M-like addressing byte/field exists.
- `example_binary`: illustrative hexadecimal test vector.

## Non-canonical status

The supplied `encoding_template` and `example_binary` values are explicitly marked as illustrative. A future canonical encoding revision must define:

1. instruction length rules;
2. endianness;
3. field alignment;
4. reserved-bit behavior;
5. extension prefixes;
6. immediate sign/zero extension;
7. register namespace width;
8. privilege encoding;
9. malformed-instruction behavior;
10. canonical assembler/disassembler serialization.

## Validation requirements

Tooling must reject or flag:

- duplicate opcode assignments;
- opcode values outside `0x0000..0xFFFF`;
- overlapping bit fields;
- field widths that do not sum to the declared instruction width;
- an `imm_size` inconsistent with `encoding_template`;
- example values that cannot fit the declared template;
- privileged instructions executed from user mode;
- undefined opcodes;
- contradictory register-field widths;
- non-zero reserved bits where the template declares them reserved.

## Architectural compatibility

The expanded encoding layer does not replace the existing R8192 semantic registry. The semantic registry remains authoritative for opcode identity and execution classification until a formal ISA encoding revision is adopted.
