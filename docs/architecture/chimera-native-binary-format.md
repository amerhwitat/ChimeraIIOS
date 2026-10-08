# Chimera Native Binary (NCB1) reference specification

Status: experimental reference format and passive parser; not yet the kernel executable loader or a stable ABI.

## Goals
NCB1 identifies the Chimera ISA, logical N-bit width, entry offset, section table, image base, and requested stack/heap limits. N-bit values are logical software/architecture-profile values; the machine still has finite RAM, address translation, buses, and resource limits. It does not promise infinite memory or universal CPU compatibility.

## Layout
All multibyte integers are little-endian. Version 1 uses the fixed 80-byte header declared by tools/binary/chimera_binary.py: magic NCB1; version; header size; flags; ISA ID; logical word width; section count; entry file offset; section-table file offset; exact file size; requested stack bytes; maximum heap bytes; preferred image base; reserved field. Accepted widths are byte-aligned 8 through 1,048,576 bits. Section records are 52 bytes: 16-byte NUL-padded ASCII name, flags, file offset, file size, memory size, alignment. Flag bit 0 means executable, bit 1 writable, bit 2 readable. Memory size may exceed file size for zero-filled BSS.

Suggested sections: .text, .rodata, .data, .bss, .reloc, .note.chimera, .symtab, .debug_*. Stack and heap are runtime mappings, not giant file sections.

A production loader must enforce W^X, page alignment, range/overflow checks, overlap/relocation rules, image trust, imports, stack/heap quotas, BSS zeroing and rollback. The prototype parser does not map pages, relocate, resolve imports, load libraries, or execute instructions.

## Compatibility
Recognition is passive. Use a compatibility matrix across format, machine, ABI, ISA extensions, dynamic loader/runtime, syscall/API translation, and trust policy. PE recognition does not provide Win32 APIs; ELF recognition does not guarantee Linux syscall compatibility; Mach-O recognition does not supply Darwin frameworks. Foreign images need a verified ABI layer or architecture emulator; unsupported operations fail closed.
