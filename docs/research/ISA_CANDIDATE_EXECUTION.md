# Chimera II OS ISA candidate execution pipeline

## Purpose and status

The canonical database remains `isa/isa_database.json`. The candidate runtime derives a candidate row for every inventoried architecture and every recorded instruction form. Architecture-only entries are explicitly discovery-only. Instruction rows retain their source reference, encoding value/mask, operands, form ID and width. Candidate presence does not imply verified hardware support.

## Modes

- **Native mapping:** maps an implemented guest mnemonic to a named Chimera semantic micro-op. This is a mapping/reference representation, not yet a native machine-code compiler or JIT.
- **Compatibility mode:** executes a small set of deterministic integer operations in a reference interpreter.
- Unsupported, privileged, memory, atomic, floating-point, vector, trap, device, and synchronization semantics are refused unless explicitly implemented. The runtime must not claim that catalog entries alone execute correctly.

## Candidate metadata

Each generated candidate records architecture/family/class, register width, mnemonic/form, operand list, syntax, encoding bits/mask, source reference, binary container families, native mapping status, compatibility execution status, and conformance status.

## RV32I executable instruction-word subset

The candidate CLI also exposes `step-rv32i`, which decodes a supplied 32-bit instruction word and executes one instruction against a 32-register state. The implemented subset includes RV32I R-type ADD/SUB/AND/OR/XOR/SLL/SRL/SRA, immediate ADDI/ANDI/ORI/XORI/SLLI/SRLI/SRAI, and LUI/AUIPC. It validates reserved upper-immediate-bit constraints for shifts, sign-extends 12-bit arithmetic immediates, masks results to 32 bits, and keeps x0 fixed at zero.

Example (ADD x1, x1, x2):

```sh
python3 tools/isa/chimera_isa_candidate.py step-rv32i --word 0x002080b3 \\
  --registers '[0,12,30,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]'
```

This is a real instruction-word decoder and bounded single-step reference execution, unlike the mnemonic-to-micro-op metadata path. It is **not** a complete RV32I implementation: branches/jumps, loads/stores, fences, ECALL/EBREAK, traps, CSRs, privilege, interrupts, virtual memory, PMP, devices, and cycle behavior remain unimplemented. Official RISC-V architectural tests and independent differential validation must pass before claiming conformance.

## Binary formats

The format catalog describes ELF, PE/COFF, Mach-O, raw instruction streams, Chimera NCB and WebAssembly. These formats are not interchangeable. A real loader must validate magic, class, endianness, machine/architecture, section bounds, relocations and ABI before execution. The current candidate tool describes formats; it is not a general-purpose executable loader and does not execute arbitrary binaries.

## Run

```sh
python3 tools/isa/chimera_isa_candidate.py list --arch riscv64
python3 tools/isa/chimera_isa_candidate.py list --supported-only --json
python3 tools/isa/chimera_isa_candidate.py inspect riscv64
python3 tools/isa/chimera_isa_candidate.py run --arch riscv64 --mnemonic ADD --lhs 12 --rhs 30 --mode compatibility
python3 tools/isa/chimera_isa_candidate.py formats --json
python3 -m unittest tests/unit/test_isa_candidate_runtime.py
```

## Normative references

- RISC-V ISA manuals: https://docs.riscv.org/reference/isa/
- Intel 64 and IA-32 Software Developer Manuals: https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html

A conformance claim requires normative-spec validation, encoder/decoder round trips, illegal-encoding tests and official or independently validated architecture tests. These are not inferred from discovery or the reference interpreter.
