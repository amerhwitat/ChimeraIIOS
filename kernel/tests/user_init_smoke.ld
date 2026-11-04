OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)
PHDRS
{
  text PT_LOAD FLAGS(5);
}
SECTIONS
{
  . = 0x0000000100000000;
  .text : ALIGN(0x1000) { *(.text .text.*) *(.rodata .rodata.*) } :text
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.data*) *(.bss*) }
}
