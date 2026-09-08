bits 16
org 0x7c00
start:
    cli
    xor ax,ax
    mov ds,ax
    mov es,ax
    mov ss,ax
    mov sp,0x7c00
    mov si,msg
.print:
    lodsb
    test al,al
    jz .halt
    mov ah,0x0e
    int 0x10
    jmp .print
.halt:
    hlt
    jmp .halt
msg db 'Chimera II / Spit Fire SF0',13,10,0
times 510-($-$$) db 0
dw 0xaa55
