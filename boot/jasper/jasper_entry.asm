[BITS 64]
global jasper_entry
extern jasper_main
section .text
jasper_entry:
    cli
    mov rsp, 0x0000000000090000
    xor rbp, rbp
    call jasper_main
.halt:
    hlt
    jmp .halt
