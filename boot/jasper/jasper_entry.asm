[BITS 64]
global jasper_entry
extern jasper_main
section .text
jasper_entry:
    cli
    call jasper_main
.halt:
    hlt
    jmp .halt
