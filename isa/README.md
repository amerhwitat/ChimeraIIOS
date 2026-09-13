# ISA database and encoding layer

`catalog.json` is the canonical, provenance-first RISC/CISC instruction database for Chimera II OS.

## Included families

RISC-V, AArch64, ARM32, MIPS32, OpenPOWER and SPARC are represented as RISC families. x86/IA-32/Intel 64/AMD64, Motorola 68000, IBM System z and VAX are represented as CISC families.

## Record model

Each instruction contains:

- stable ID and ISA family
- mnemonic and concrete assembly syntax
- operand list and operand kinds
- explicit optional operands and defaults when applicable
- instruction length
- encoding fields/template
- exact worked binary encoding
- exact equivalent hexadecimal encoding
- provenance at catalog level

## Decoder/assembler roadmap

The catalog is deliberately suitable for a future generic decoder:

`bytes -> family selector -> length decoder -> opcode/mask -> operand-field extraction -> semantic instruction -> Chimera IR`

and assembler:

`semantic instruction + operands -> family encoder -> fields -> endian/byte serialization -> machine code`

x86 must retain prefix/REX/VEX/EVEX/APX-aware variable-length handling; RISC-V must retain 16-bit compressed and future variable-length rules; A64/ARM/MIPS/POWER/SPARC use their respective fixed-width field models.

The current catalog is a curated compatibility baseline, not a claim that every instruction, extension or microarchitectural feature has already been encoded. New entries should be added from normative specifications and checked against independent assembler/disassembler sources where possible.
