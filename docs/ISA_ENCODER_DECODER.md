# ISA Schema-Driven Encoder/Decoder

The Chimera II ISA toolchain now exposes a C++ encoder/decoder facade over the generated `isa_bitfields.json` registry.

## Design

`include/chimera/ISA_EncoderDecoder.hpp` and `src/isa/ISA_EncoderDecoder.cpp` provide:

- mnemonic lookup through the existing `BitfieldRegistry`;
- schema-driven opcode and operand placement;
- schema-driven decoding;
- a 128-bit logical instruction container (`lo` + `hi`);
- strict rejection of `canonical_abi_only` and `template_review_required` records;
- operand width validation;
- preservation of the existing 16-byte instruction ABI.

The supplied `nlohmann::json` implementation was intentionally adapted rather than copied verbatim. Chimera II already has a dependency-free JSON reader, so the core build does not acquire a mandatory third-party dependency.

## ABI

The emulator packet remains exactly:

`opcode[16] | rd[16] | rs[16] | rt[16] | immediate[64]`

or 16 bytes. The `InstructionWord128` type represents that complete logical container without changing the wire/ABI contract.

## Example

```cpp
BitfieldRegistry registry;
std::string error;
if (!registry.load_file("isa_bitfields.json", &error)) {
    throw std::runtime_error(error);
}

ISAEncoderDecoder codec(registry);
auto word = codec.encode("ADD", {{"rd", 1}, {"rs", 2}, {"rt", 3}});
auto operands = codec.decode("ADD", word);
```

## Sample generation

`tools/isa/generate_encoder_decoder_sample.py` creates a deterministic 30-instruction fixture from the generated canonical registry. This avoids manually duplicating or silently changing ISA metadata.

Example:

```bash
python3 tools/isa/generate_isa_bitfields.py --output build/isa_bitfields.json
python3 tools/isa/generate_encoder_decoder_sample.py build/isa_bitfields.json build/isa_encoder_decoder_sample.json
```

The fixture is deliberately derived from the authoritative opcode table and therefore follows future ISA metadata changes automatically.

## Compatibility rule

A recognized opcode is not automatically considered safely encodable. Only records whose metadata has `encoding_status=template` are accepted by this facade. Review-required and canonical-ABI-only records remain visible to tooling but fail closed for logical-template encoding until their metadata is resolved.
