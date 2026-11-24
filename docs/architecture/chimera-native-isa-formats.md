# Chimera-native ISA formats (engineering evidence)

This document describes the derived native-ISA representation added under
`tools/isa/`. It is a bounded vertical slice, **not** a claim of full catalogue
conformance and **not** a release gate for an ISO.

## Policy and scope

- The official inventory `isa/generated/universal-instruction-catalog.json` is
  **read-only** here. Its `coverage.conformance_tested` stays `0` and
  `coverage.not_implemented` stays `1613`.
- The derived catalogue `isa/generated/chimera-native-isa-catalog.json` contains
  all **104** architecture inventory entries and all **1613** instruction rows.
  Every row is normalised with architecture-owned semantics, native format
  descriptors, operand/option/implementation/effect fields and a status that
  is honest about whether a real backend exists.
- `isa_database.json` `class` is authoritative for architecture family /
  RISC-vs-CISC classification. Source instruction bytes remain in their source
  ISA encoding; nothing is flattened into an invented Chimera opcode.
- Rows without a real encoder/decoder/executor are explicitly
  `implementation.status = "not_implemented"` with a reason. Having a sourced
  fixed-bit mask is a **descriptor**, not an implementation.

## Implemented real backend slice

| Architecture | Family | Encoding implemented |
| --- | --- | --- |
| `x86-64` | CISC | REX prefix, opcode, ModRM, optional SIB, disp8/disp32, rel32, stack and fixed forms |
| `aarch64` | RISC | Fixed 32-bit data-processing, add/sub immediate, load/store unsigned offset, branches, hints, system |
| `riscv64` | RISC | RV64I R/I/S/B/U/J/system 32-bit encodings with 64-bit register semantics |

`tools/isa/chimera_native_isa.py` provides `assemble`, `disassemble`, `step`,
`effects` and the `CHMOBJ1` object writer/validator for these architectures.
`tools/chimera-asm/chimera_native_formats.json` extends the `CHM-ISA-1`
canonical-uop definition in `tools/chimera-asm/chimera_isa.json` with these
native format descriptors and the 104-entry inventory, without changing the
base file.

## Versioned object format: `CHMOBJ1`

- 64-byte header with magic `CHMOBJ1\0`, format version, ABI version, CRC32
  architecture id, flags, section/symbol/relocation counts and table offsets.
- Section table (`NULL`, `PROGBITS`, `NOBITS`, `STRTAB`, `SYMTAB`, `RELATAB`,
  `NOTE`) with per-section permission flags and power-of-two alignment.
- Symbol table and relocation table (`ABS64`, `ABS32`, `REL32`).
- SHA-256 footer over the body; the loader recomputes it and strictly rejects
  bad magic/version/ABI, unknown architecture ids, overlapping or out-of-bounds
  tables, bad alignment, invalid symbol/relocation records and digest mismatch.

## Conformance evidence

`tools/isa/run_native_isa_conformance.py` produces
`isa/generated/native-isa-conformance-evidence.json` with measured results for:

- encode/decode round trips against the sourced fixed-bit masks,
- execution vectors with register, flag, memory, PC and trap comparisons,
- illegal-encoding rejection,
- cross-checks against the existing `tools/isa/riscv_codec.py` /
  `tools/isa/rv32_machine.py` RV32I base subset (low 32 bits only),
- valid and deliberately malformed `CHMOBJ1` objects.

The current run is **128/128 engineering checks passed** for the implemented
slice. This is explicitly labelled `partial-engineering-evidence-only`. It does
not certify the remaining 1554 rows and never updates official counts.

## Rebuild and verification

```bash
bash tools/isa/rebuild_native_isa.sh            # regenerate derived outputs
bash tools/isa/rebuild_native_isa.sh --check    # verify committed outputs
python -m pytest tests/isa/test_native_isa_formats.py -q
```

`kernel/build-koronos.sh` calls the `--check` form after
`tools/isa/generate_registry.py` unless `CHIMERA_SKIP_NATIVE_ISA_CHECK=1` is
set. `.github/workflows/isa-native-formats.yml` runs the same checks plus an
explicit baseline assertion.

## Known gaps

- Only 59 of 1613 instruction rows have a real backend; the remaining 1554 are
  descriptors-only/not-implemented and are reported as such.
- CISC coverage is register/base-index-displacement and branches only; no
  immediate ALU forms, no x87/SIMD, no privileged x86 instructions.
- AArch64 coverage excludes the zero register, shifts other than LSL #0,
  conditional branches and most system instructions.
- RV64I coverage excludes `LB`/`LH(U)` sign-extension variants beyond `LH`,
  multiplication/division, atomics, compressed/`RVC`, and privileged CSR forms.
- Execution vectors are a tiny hand-written set, not a full architectural test
  suite. The RV32 reference comparison covers only the shared base subset.
