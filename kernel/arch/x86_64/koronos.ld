OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)
SECTIONS {
 . = 0x100000;
 .text : ALIGN(4096) { KEEP(*(.text.boot)) *(.text*) }
 .rodata : ALIGN(4096) { *(.rodata*) }
 .data : ALIGN(4096) { *(.data*) }
 .bss : ALIGN(4096) { *(COMMON) *(.bss*) }
 .koronos.modules : ALIGN(4096) {
  __koronos_modules_start=.;
  KEEP(*(.koronos.module))
  __koronos_modules_end=.;
 }
}
