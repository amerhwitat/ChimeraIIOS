# CISC and RISC mapping to C8192 and R8192

## Canonical rule

- Every catalogue row classified as `CISC` maps to `chimera-c8192`.
- Every catalogue row classified as `RISC` maps to `chimera-r8192`.
- CISC extensions map through their owning CISC frontend to C8192; RISC extensions map through their owning RISC frontend to R8192.
- Chimera's project-defined C8192 and R8192 retain their own native identities.

C8192 is the 8192-bit-register CISC target with variable-width instruction packets. R8192 is the 8192-bit-register RISC target with fixed 64-bit instruction packets. The source ISA's original instruction width is not changed by this mapping.

## Required lowering path

`guest bytes -> ISA-specific decoder -> validated instruction descriptor -> canonical MicroOp -> C8192/R8192 execution backend`

Each decoder must preserve operand widths, addressing modes, register aliases, condition flags, memory ordering, atomicity, privilege checks, exceptions, vector state, and ABI rules. Translation is instruction- and feature-specific. There is no valid universal rule that maps a guest opcode number directly onto a C8192/R8192 opcode number.

EPIC, VLIW, DSP, GPU and VM instruction sets retain dedicated bundle-, packet-, device- or sandbox-aware backends. They are not silently misclassified as CISC or RISC.

## Coverage and status

`isa/cpu_isa_target_map.json` contains one mapping row for every architecture in `isa/isa_database.json`, including inventory-only entries. `tools/isa/map_cpu_isa.py --validate` checks that the map exactly covers the current catalogue and that CISC/RISC assignments remain correct. `python3 tests/isa/test_cpu_isa_target_map.py` runs regression tests.

A map row is not evidence of a complete decoder, assembler, disassembler, compiler backend, emulator, native binary, or conformance result. Those require real implementation and architecture-specific test vectors. Catalogue-only entries remain discovery targets until their authoritative encodings and semantics are implemented and verified.
