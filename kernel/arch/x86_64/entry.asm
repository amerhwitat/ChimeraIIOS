[BITS 64]
section .text
extern koronos_boot_entry
global _start
_start:
    cld
    mov rsp, stack_top
    mov rdi, rbx
    call koronos_boot_entry
.hang:
    hlt
    jmp .hang
section .bss
align 16
stack_bottom: resb 16384
stack_top:
