# Native Chimera assembler/disassembler

This toolchain recognizes the Chimera Bit Mode ISA independently of the host ISA.

Commands:

- `chimera-as` — source -> Chimera object/bytecode.
- `chimera-objdump` — object -> assembly, symbols and relocation records.
- `chimera-dis` — raw Chimera bytes -> canonical instructions.
- `chimera-re` — reverse-engineering view: sections, control-flow boundaries, register usage, call/jump targets and host-ISA provenance.

Instruction encoding is versioned and width-neutral. A RegisterN operand carries an explicit width field, so 8192-bit and larger programs share the same decoder. Host instructions are never misidentified as Chimera instructions; binaries must declare their machine type in the CHM ELF note/metadata.
