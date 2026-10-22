OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)

/* Minimal user-mode ELF image layout used by Koronos native-init acceptance
 * payloads. Keep executable and writable segments separate (W^X); the kernel
 * ELF loader maps PT_LOAD entries and zero-fills p_memsz - p_filesz. */
PHDRS
{
  text PT_LOAD FLAGS(5); /* PF_R | PF_X */
  data PT_LOAD FLAGS(6); /* PF_R | PF_W */
}

SECTIONS
{
  . = 0x400000;
  .text : ALIGN(0x1000)
  {
    KEEP(*(.text.boot))
    *(.text .text.*)
  } :text

  .rodata : ALIGN(0x1000)
  {
    *(.rodata .rodata.*)
    *(.eh_frame .eh_frame.*)
  } :text

  . = ALIGN(0x1000);
  .data :
  {
    *(.data .data.*)
  } :data

  .bss :
  {
    *(COMMON)
    *(.bss .bss.*)
  } :data

  /DISCARD/ :
  {
    *(.comment)
    *(.note .note.*)
  }
}
