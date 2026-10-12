# ISA source discovery, register effects, and mode mapping

## Build-time discovery

Run `python3 tools/isa/crawl_sources.py --refresh` to refresh the source discovery index. The ISO build may opt in with `--refresh-online-catalogs`. Source discovery uses a versioned manifest and stores SHA-256 hashes, resolved URLs, fetch times, byte counts, and cache paths. Network failures are recorded and do not silently erase the last known index.

Discovery is not ingestion. Official manuals are linked as references; only machine-readable, license-reviewed data should be adapted into instruction rows. A source page mentioning an instruction is not proof of a valid encoding, exact architectural effects, or working execution.

## Required per-form properties

Preserve when authoritative data supports them: opcode/mask, instruction length and prefix constraints, illegal/reserved encodings, operand kinds and widths, signedness, immediate extraction/sign extension, register aliases and implicit operands, register reads/writes and partial-register effects, condition flags, vector/predicate and floating-point state, control/system registers, memory effects and ordering, exceptions/traps, privilege, feature gates, instruction byte order separately from data endianness, source revision/hash/license, validation status, semantic implementation status, and conformance-test references.

Unknown effects must remain `unknown`; never infer register effects from mnemonic names alone.

## Native and compatibility register mapping

The native path maps guest architectural state to explicit Chimera semantic state/micro-ops; it is not automatically host machine-code generation. Compatibility execution must preserve guest-observable semantics, including register width, zero-register behavior, partial-register writes, flags, floating-point state, privilege state, memory ordering, and traps. State without a backend equivalent must be emulated explicitly or rejected.

Mappings must encode per-architecture register files and alias rules rather than one name-to-name table. Examples that require different semantics include x86 subregister writes, AArch64 W-register writes zero-extending into X registers, and RISC-V x0 discarding writes. Test these independently.

## Endianness

Track instruction encoding byte/parcel order, data-memory byte order, and ABI/object-file byte order separately. They are not universally identical. RISC-V instruction parcels are little-endian even when an execution environment supports big-endian data accesses. Bi-endian families need an explicit active mode and instruction-specific exceptions; do not flatten them to a single family-wide value.

## Acceptance gates

1. Schema and provenance validation pass.
2. Encodings are validated against an authoritative source or decoder table.
3. Register/flag/memory/trap effects are sourced or explicitly unknown.
4. Native mapping and compatibility semantics are independently tested.
5. Official architecture test suites pass before marking a form `conformance-tested`.
6. Report sourced forms, encoding-validated forms, implemented forms, and conformance-tested forms separately.
