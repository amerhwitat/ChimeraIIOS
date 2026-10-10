/* Minimal Multiboot v1 entry for the independent Koronos 32-bit bring-up target.
 * This is a test harness, not yet the production Koronos kernel entry. */
.set MB_ALIGN,    1<<0
.set MB_MEMINFO,  1<<1
.set MB_FLAGS,    MB_ALIGN | MB_MEMINFO
.set MB_MAGIC,    0x1BADB002
.set MB_CHECKSUM, -(MB_MAGIC + MB_FLAGS)

.section .multiboot
.align 4
.long MB_MAGIC
.long MB_FLAGS
.long MB_CHECKSUM

.section .text
.global _start
.type _start, @function
.extern koronos32_main
_start:
    cli
    mov $stack_top, %esp
    xor %ebp, %ebp
    call koronos32_main
1:  cli
    hlt
    jmp 1b

.section .bss
.align 16
stack_bottom:
.skip 16384
stack_top:
