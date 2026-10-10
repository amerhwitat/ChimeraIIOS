# Chimera II OS ISA candidate execution pipeline

## Purpose and status

The canonical database remains `isa/isa_database.json`. The candidate runtime derives a candidate row for every inventoried architecture and every recorded instruction form. Architecture-only entries are explicitly discovery-only. Instruction rows retain their source reference, encoding value/mask, operands, form ID and width. Candidate presence does not imply verified hardware support.

## Modes

- **Native mapping:** maps an implemented guest mnemonic to a named Chimera semantic micro-op. This is a mapping/reference representation, not yet a native machine-code compiler or JIT.
- **Compatibility mode:** executes a small set of deterministic integer operations in a reference interpreter.
- Unsupported, privileged, memory, atomic, floating-point, vector, trap, device, and synchronization semantics are refused unless explicitly implemented. The runtime must not claim that catalog entries alone execute correctly.

## Candidate metadata

Each generated candidate records architecture/family/class, register width, mnemonic/form, operand list, syntax, encoding bits/mask, source reference, binary container families, native mapping status, compatibility execution status, and conformance status.

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
