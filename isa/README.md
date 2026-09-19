# Chimera II ISA Registry

This directory is the machine-readable ISA boundary for Chimera II OS.

## Files

- `world_architectures.json` — ISA family and target index.
- `isa_database.json` — canonical instruction rows with operands and binary value/mask patterns.
- `instructions.json` — export contract and schema reference.
- `isa_database.sql` — SQLite schema.
- `spec/chimera_isa.yaml` — native R8192/C8192 profiles, encoding model, opcode ranges, assembler pipeline, directives, pseudo-instructions, and compatibility boundary.
- `spec/risc-cisc-assemblers.md` — traceability and design integration for the attached RISC/CISC/assembler lecture.

## Native profiles

**R8192** is the fixed-width RISC-oriented profile: 64-bit instructions, 1024 8192-bit registers, 256 predicate bits, register-oriented operations, and explicit load/store memory access.

**C8192** is the CISC-oriented profile: explicit 64/128/256/512/1024/2048/4096-bit packets using the same 8192-bit register model and a canonical micro-op lowering boundary.

These are project-defined profiles. They do not claim that the attached Cornell lecture specifies Chimera hardware.

## Binary encoding convention

Every instruction row stores:

1. `length_bits` — width represented by the binary pattern.
2. `value_bits` — a concrete encoding example or fixed opcode/control pattern.
3. `mask_bits` — `1` means the corresponding bit is fixed; `0` means the bit is selected by an operand, displacement, register field or extension field.

This avoids the incorrect assumption that a parameterized instruction such as x86 `ADD r/m64,r64` has one universal binary value. Parameterized instructions have fixed opcode bytes plus operand-dependent fields.

For native Chimera, the base 64-bit packet contains a 16-bit opcode selector and three 16-bit operand selectors; immediate/address information is carried by explicit extensions. C8192 larger packets are explicit packet widths, not implicit variable-length byte strings.

## RISC/CISC and assembler integration

The attached source, *RISC, CISC, and Assemblers* by Hakim Weatherspoon (CS 3410, Spring 2012, Cornell University), covers ISA variations, RISC/CISC tradeoffs, fixed and variable instruction formats, assembly instructions, pseudo-instructions, data/layout directives, object-file staging, two-pass assembly, and executable-program construction. fileciteturn30file0L84-L95 fileciteturn30file0L164-L218

Chimera incorporates those concepts as toolchain architecture: first-pass symbol/layout construction, second-pass encoding/relocation, `.text`/`.rodata`/`.data`/`.bss` separation, and deterministic pseudo-instruction lowering. The source specifically describes assembly as instructions plus pseudo-instructions plus data/layout directives and describes two-pass label resolution. fileciteturn30file0L319-L331 fileciteturn30file0L365-L374 fileciteturn30file0L409-L424

## Coverage

The family registry covers Chimera C8192/R8192, x86/x86-64, AArch64/A32, RISC-V 32/64, MIPS 32/64, Power ISA, SPARC V9, Motorola 68000, IBM z/Architecture, VAX, SuperH, LoongArch, Alpha, PA-RISC, Xtensa, AVR, MCS-51/8051, Z80, 6502 and IA-64/Itanium.

The instruction corpus focuses on core forms useful to the Chimera universal decoder: integer ALU, logical operations, loads/stores, immediate forms, branches, calls/returns, system operations and Chimera-native research operations. A family with `instruction_forms: 0` is enumerated but deliberately has no invented instruction encodings.

## Validation

```bash
python tools/validate_isa_registry.py
python tools/isa_registry_report.py
python tools/load_isa_database.py --output isa/isa.db
pytest -q tests/test_isa_registry.py
```

The SQLite file `isa/isa.db` is generated output and should not be hand-edited; regenerate it from the canonical JSON.

## Source boundary

The lecture is used only for concepts and terminology relevant to ISA/assembler design. External architecture encodings remain attributed to their respective architecture specifications; Chimera-native encodings remain project-defined.
