.section .multiboot
.align 8
.long 0xE85250D6
.long 0
.long header_end - multiboot_header
.long -(0xE85250D6 + 0 + (header_end - multiboot_header))
.word 0
.word 0
.long 8
header_end:

.section .text
.global _start
.type _start,@function
_start:
    cli
    mov $stack_top, %esp
    push %ebx
    push %eax
    call chimera_boot_main
1:
    hlt
    jmp 1b

.section .bss
.align 16
stack_bottom:
.skip 16384
stack_top:
