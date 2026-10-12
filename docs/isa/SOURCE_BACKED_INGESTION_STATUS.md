# Source-backed ISA ingestion status

## Current implementation

- `tools/isa/crawl_sources.py --refresh` refreshes the configured source discovery index and records hashes/status.
- `tools/isa/import_riscv_opcodes.py` fetches the upstream `riscv-opcodes` repository tree and parses fixed-bit encoding declarations from extension files.
- `tools/isa/build_universal_catalog.py --input isa/sources/imports/riscv-opcodes.json` merges those imported encoding rows into the universal catalog.
- `build-chimera-iso.sh --refresh-online-catalogs` opts into source refresh and the RISC-V opcode import before normal preflight.

## What is and is not imported

The RISC-V adapter imports encoding masks and source provenance. It intentionally does **not** infer register read/write effects, flags, memory behavior, traps, privilege checks, or semantics from an instruction mnemonic. Those properties must come from an authoritative semantic description or remain unknown. Imported forms remain `not-implemented` until an execution implementation exists.

The RISC-V opcode importer pins upstream commit `5783cf3bea312a48d28e3e2c8a2fcb55603e4bed` by default, records the immutable revision in each row, and accepts an explicit `--revision` override only when it is a 40-character commit SHA. Review and update this pin intentionally when refreshing the source catalog. Review licensing and source terms before redistributing imported data.

## Next family adapters

LLVM TableGen contains register aliases/classes and implicit uses/definitions, and target instruction descriptions expose instruction properties; these are useful machine-readable inputs but require per-target adapters and license/provenance handling. RISC-V UnifiedDB additionally models extensions, instruction specifications, CSR specifications, and operation descriptions. See:

- https://github.com/riscv/riscv-opcodes
- https://github.com/riscv/riscv-unified-db
- https://github.com/llvm/llvm-project/tree/main/llvm/lib/Target
- https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
- https://developer.arm.com/documentation/

## Verification gates

Do not label a record executable or conformant based on successful import. Required separate gates are: schema validation, encoding validation, sourced architectural effects, implementation tests, and official architecture conformance tests. Build and boot validation are separate from ISA validation.
