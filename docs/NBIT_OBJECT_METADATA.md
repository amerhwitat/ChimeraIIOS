# CHIR-NIR object metadata v1

This directory defines the portable metadata contract for N-bit code objects.
It is deliberately a sidecar JSON contract until each platform object writer and
linker has implemented a native section and relocation semantics.

Required fields:
- format: `CHIR-NIR-META`
- version: integer 1
- target: explicit architecture and ABI
- helper_abi: `CHIMERA_NBIT_ABI_VERSION`
- values: symbol, kind, width, signedness, optional fixed-point fractional bits
- source_map: object symbol and source file/line/column
- helpers: external helper names and their required ABI version

Linkers should reject unknown major versions, target/ABI mismatches, conflicting
symbol types, and helper ABI mismatches. Debuggers and decompilers should retain
the declared width and signedness rather than infer them from the host register.
Do not treat this JSON sidecar as a native ELF/Mach-O/COFF section; those writers
must encode and validate it before claiming native object integration.
