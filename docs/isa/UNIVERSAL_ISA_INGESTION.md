# Universal ISA catalog ingestion and translation

The canonical ISA database remains `isa/isa_database.json`. The legacy positional
instruction rows do **not** have room for every property required by an assembler,
decoder, binary translator, emulator, or conformance suite, so
`tools/isa/build_universal_catalog.py` generates the normalized sidecar
`isa/generated/universal-instruction-catalog.json`.

## Properties represented per form

Architecture and mnemonic; form and operand schema; syntax and description;
instruction width; opcode/value and fixed-bit mask; encoding format; instruction
byte order and data/operand endianness; immediate fields; register classes;
flags read/written; memory effects; privilege level; required extensions and
features; exceptions; semantic identifier; native and compatibility mappings;
encoding and execution status; source reference, revision, digest, and license.

Missing facts remain null or explicitly unspecified. The importer does not
fabricate opcode masks or infer that an instruction is executable just because it
is listed.

## Importing sourced entries

Create a JSON file containing an array of instruction objects (or an object with
an `instructions` array), and run:

```sh
python3 tools/isa/build_universal_catalog.py --input /path/to/sourced-instructions.json
```

Repeat `--input` for each architecture/extension dataset. The normalizer
validates fixed-bit strings, keeps distinct instruction forms, deduplicates exact
duplicates, and reports how many forms have sourced masks and how many are
actually implemented or conformance-tested.

Only ingest data when its source terms permit redistribution. Keep source
revision and license metadata with the records. Prefer vendor/standards machine
readable tables and maintained assembler/disassembler opcode tables over scraping
unstructured manuals. Examples of authoritative references:

- Intel SDM: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
- RISC-V specifications: https://docs.riscv.org/reference/isa/
- RISC-V source repository: https://github.com/riscv/riscv-isa-manual

## Binary and mode semantics

`tools/isa/translate_encoding_bytes.py` provides bit-string/byte serialization
for little-endian, big-endian, and fixed-little-endian instruction parcels. This
is a byte-order utility, not a universal disassembler: variable-length x86,
Thumb, RISC-V parcels, and architecture-specific operand/immediate fields still
require architecture-specific decoders.

- **Compatibility mode** must decode the source ISA, translate to a canonical
  semantic representation, and execute only semantics implemented by a backend.
- **Native mode** means execution by a native Chimera backend or a proven lowering
  to a supported target. It does not mean that a catalog row is natively
  executable.
- Unsupported instructions, privilege effects, atomics, memory ordering, traps,
  and device effects must fail closed until implemented and tested.
- Mark a form `conformance-tested` only when it passes applicable official tests
  or a documented equivalent test suite.

The generated count is the count of records actually supplied to the importer;
this repository does not claim that the current catalog already contains 5,000
verified instruction forms or that all catalogued forms execute.
