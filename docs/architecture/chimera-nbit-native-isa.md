# Chimera N-bit native ISA — current project-defined subset

Status: research ISA catalogue, not yet a complete compiler/backend or kernel execution engine.

## Design constraints

The ISA ID in NCB1 identifies a versioned Chimera execution profile. Logical register width is independent of virtual-address width, physical-address width, page size, and memory bus transaction width. Current experimental N-bit work uses a finite software interpreter with bounded widths; it is not a claim of infinite physical CPU resources.

## Current catalogue subset

The canonical partial source is isa/isa_database.json, architecture chimera-c8192. The currently listed forms use a 16-bit opcode selector plus operand subfields:

| Mnemonic | Pattern prefix | Catalog syntax | Status |
|---|---|---|---|
| ADD | 0001 | ADD Z0,Z1 | documented/catalogued; verify operand encoding before execution |
| MUL | 0010 | MUL Z0,Z1 | documented/catalogued; verify operand encoding before execution |
| TCONTRACT | 0011 | TCONTRACT Z0,Z1,Z2 | project-defined research operation |
| MODEXP | 0100 | MODEXP Z0,Z1,Z2 | project-defined research operation |
| NETSEND | 0101 | NETSEND Z0,P0 | project-defined research operation |

These prefixes are inventory metadata, not a stable machine-code ABI. Register IDs, immediate formats, trap semantics, memory ordering, privilege transitions, syscalls, relocations and exact operand bitfields must be normatively specified before a production compiler can emit binaries. NCB1 currently stores the ISA identifier but does not make these instruction forms executable.

## Required implementation sequence

1. Freeze a versioned ISA and exact bitfield/opcode/operand tables.
2. Implement assembler, encoder, decoder, disassembler and malformed/illegal encoding rejection.
3. Implement a reference interpreter and golden instruction tests.
4. Define syscall ABI, ELF/NCB loader integration, dynamic linker and runtime libraries.
5. Add conformance tests and cross-build reproducibility.
6. Only then mark each form encoded, decoded, executed, and conformance-tested in the database.
