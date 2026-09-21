OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
 . = 0x80200000;
 .text : ALIGN(4096) { KEEP(*(.text.boot)) *(.text*) }
 .rodata : ALIGN(4096) { *(.rodata*) }
 .data : ALIGN(4096) { *(.data*) }
 .bss : ALIGN(4096) { *(COMMON) *(.bss*) }
 .koronos.modules : ALIGN(4096) { KEEP(*(.koronos.module)) }
}
