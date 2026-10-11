OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)
PHDRS
{
  text PT_LOAD FLAGS(5);
  data PT_LOAD FLAGS(4);
}
SECTIONS
{
  . = 0x4000000000;
  .text : ALIGN(0x1000) { *(.text .text.*) } :text
  .rodata : ALIGN(0x1000) { *(.rodata .rodata.*) } :data
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
