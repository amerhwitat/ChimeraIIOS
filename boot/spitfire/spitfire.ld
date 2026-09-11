OUTPUT_FORMAT(binary)
ENTRY(start)
SECTIONS {
  . = 0x7E00;
  .text : ALIGN(16) { *(.text*) }
  .rodata : ALIGN(16) { *(.rodata*) }
  .data : ALIGN(16) { *(.data*) }
  .bss : ALIGN(16) { *(COMMON) *(.bss*) }
  .bootinfo : ALIGN(16) { *(.bootinfo*) }
}
