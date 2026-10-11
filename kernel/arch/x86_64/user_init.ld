OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(chimera_user_init_entry)
PHDRS
{
  text PT_LOAD FLAGS(5);
  data PT_LOAD FLAGS(6);
}
SECTIONS
{
  . = 0x0000004000000000;
  .text : ALIGN(4096) { *(.text*) *(.rodata*) } :text
  . = ALIGN(4096);
  .data : { *(.data*) } :data
  .bss : { *(COMMON) *(.bss*) } :data
  /DISCARD/ : { *(.comment*) *(.note*) *(.eh_frame*) }
}
