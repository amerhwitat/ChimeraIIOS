OUTPUT_ARCH(aarch64)
ENTRY(_start)
SECTIONS {
 . = 0x40080000;
 .text : ALIGN(4096) { KEEP(*(.text.boot)) *(.text*) }
 .rodata : ALIGN(4096) { *(.rodata*) }
 .data : ALIGN(4096) { *(.data*) }
 .bss : ALIGN(4096) {
   *(COMMON) *(.bss*)
   . = ALIGN(16);
   __stack_bottom = .;
   . += 16384;
   __stack_top = .;
 }
 .koronos.modules : ALIGN(4096) { KEEP(*(.koronos.module)) }
}
