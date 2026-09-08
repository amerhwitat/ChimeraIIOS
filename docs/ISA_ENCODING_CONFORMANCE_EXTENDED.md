# Chimera II ISA Encoding Conformance — Extended Metadata

## Scope

This specification applies to the extended machine-readable ISA metadata beginning with `ECC_POINT_ADD` (`0x0043`) and continuing through the complete supplied `DMABUF_EXPORT` record (`0x0091`).

It is a tooling and validation specification. It does not redefine the architectural opcode ABI.

## Validation rules

### 1. Identity

Every row must contain a unique `(mnemonic, opcode)` identity. If an opcode already exists in the semantic ISA catalog, the metadata row must refer to the same instruction rather than create a second semantic meaning.

### 2. Opcode representation

The `opcode` column is the semantic opcode identifier. `opcode_bits` is the compact encoding-level opcode representation and must be checked independently because the supplied metadata uses both 8-bit encoding examples and 16-bit semantic opcode notation.

### 3. Encoding width

Templates may describe 32-, 48-, 64-, or 128-bit layouts. The validator must calculate field widths and compare them with the example binary length. Disagreement is a conformance warning/error depending on whether the row is marked illustrative or canonical.

### 4. Immediate fields

`imm_size` must not exceed the explicitly allocated immediate field. Pointer-like fields such as `path_ptr120`, `out_ptr120`, and `cmd_buf_ptr120` are operands, not automatically immediate constants.

### 5. Privilege

Allowed classes are `user` and `priv`. `priv` operations require kernel/capability mediation. User-mode classification does not bypass address, handle, object, or capability validation.

### 6. ModRM-like metadata

`modrm_like=yes` indicates an encoding/decoder form requiring an additional addressing/modifier interpretation. It does not imply x86 compatibility.

### 7. Example binaries

`example_binary` values are test vectors supplied as illustrative examples. They must be parsed as hexadecimal and checked for width consistency. Tooling must report malformed examples instead of changing them silently.

## Canonical emulator boundary

The current Chimera II emulator uses its established canonical instruction container and execution path. The expanded encoding metadata therefore feeds assembler/disassembler/decoder-generation tooling without silently changing the emulator's host ABI.

A future native variable-width instruction ABI requires an explicit architecture revision and compatibility specification.

## Pending source records

- The text immediately preceding `ECC_POINT_ADD` is incomplete and has no reliable mnemonic/opcode identity.
- `PIPEWIRE_PUBLISH` at `0x0092` is incomplete in the supplied source. It must be added only after the complete row is supplied.

No values have been invented for either boundary.
