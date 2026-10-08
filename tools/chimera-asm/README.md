# Native Chimera assembler/disassembler

This toolchain recognizes the Chimera Bit Mode ISA independently of the host ISA.

Commands:

- `chimera-as` — source -> Chimera object/bytecode.
- `chimera-objdump` — object -> assembly, symbols and relocation records.
- `chimera-dis` — raw Chimera bytes -> canonical instructions.
- `chimera-re` — reverse-engineering view: sections, control-flow boundaries, register usage, call/jump targets and host-ISA provenance.

Instruction encoding is versioned and width-neutral. A RegisterN operand carries an explicit width field, so 8192-bit and larger programs share the same decoder. Host instructions are never misidentified as Chimera instructions; binaries must declare their machine type in the CHM ELF note/metadata.

## Experimental NCB1 bridge

- `chimera-ncb-as.sh input.asm output.ncb [word-bits] [isa-id]` compiles the current fixed 16-byte record assembler and packages its code stream in a validated NCB1 `.text` section.
- `chimera-ncb-dis.py output.ncb` validates the NCB1 container and disassembles that prototype `.text` record stream.
- The bridge preserves the distinction between a structured NCB1 container and a finished native executable ABI. It does not add labels, relocations, imports, a C/C++ backend, or kernel execution support.
