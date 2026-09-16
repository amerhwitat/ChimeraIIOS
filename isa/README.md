# Chimera II ISA Registry

This directory is the machine-readable ISA boundary for Chimera II OS.

## Files

- `world_architectures.json` — ISA family and target index.
- `isa_database.json` — canonical instruction rows with operands and binary value/mask patterns.
- `instructions.json` — export contract and schema reference.
- `isa_database.sql` — SQLite schema.

## Binary encoding convention

Every instruction row stores:

1. `length_bits` — width represented by the binary pattern.
2. `value_bits` — a concrete encoding example or fixed opcode/control pattern.
3. `mask_bits` — `1` means the corresponding bit is fixed; `0` means the bit is selected by an operand, displacement, register field or extension field.

This avoids the incorrect assumption that a parameterized instruction such as x86 `ADD r/m64,r64` has one universal binary value. Parameterized instructions have fixed opcode bytes plus operand-dependent fields.

## Coverage

The family registry covers Chimera C8192/R8192, x86/x86-64, AArch64/A32, RISC-V 32/64, MIPS 32/64, Power ISA, SPARC V9, Motorola 68000, IBM z/Architecture, VAX, SuperH, LoongArch, Alpha, PA-RISC, Xtensa, AVR, MCS-51/8051, Z80, 6502 and IA-64/Itanium.

The instruction corpus focuses on core forms useful to the Chimera universal decoder: integer ALU, logical operations, loads/stores, immediate forms, branches, calls/returns, system operations and Chimera-native research operations. A family with `instruction_forms: 0` is enumerated but deliberately has no invented instruction encodings.

## Sources

Authoritative references are linked in `isa_database.json`. Current primary-source references include RISC-V International, Arm, Intel, AMD, OpenPOWER, Oracle SPARC, IBM z/Architecture, MIPS, Microchip AVR and Zilog. citeturn0search0turn0search1turn0search2turn0search4turn0search11

For RISC-V, the official documentation separates base integer ISAs from optional extensions and defines fields such as `funct7`, `rs2`, `rs1`, `funct3`, `rd` and `opcode`; the current ratified library includes many standard extensions beyond the base. citeturn0search6turn0search7

For AArch64/A32, Arm documentation describes fixed A64 encodings and fielded A32/A64 load/store and arithmetic formats. citeturn1search0

## Validation

```bash
python tools/validate_isa_registry.py
python tools/isa_registry_report.py
python tools/load_isa_database.py --output isa/isa.db
pytest -q tests/test_isa_registry.py
```

The SQLite file `isa/isa.db` is generated output and should not be hand-edited; regenerate it from the canonical JSON.
