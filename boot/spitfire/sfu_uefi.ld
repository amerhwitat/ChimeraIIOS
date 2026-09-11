OUTPUT_FORMAT(elf_x86_64)
ENTRY(efi_main)
SECTIONS {
  .text : ALIGN(4096) { *(.text*) }
  .rodata : ALIGN(4096) { *(.rodata*) }
  .data : ALIGN(4096) { *(.data*) }
  .reloc : ALIGN(4096) { *(.reloc*) }
  .bss : ALIGN(4096) { *(COMMON) *(.bss*) }
}
