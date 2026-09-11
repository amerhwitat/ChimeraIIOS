[BITS 16]
[ORG 0x7C00]
start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti
    mov [boot_drive], dl
    mov si, dap
    mov dl, [boot_drive]
    mov ah, 0x42
    int 0x13
    jc .error
    jmp 0x0000:0x7E00
.error:
    mov si, msg_fail
.print:
    lodsb
    test al, al
    jz .halt
    mov ah, 0x0E
    int 0x10
    jmp .print
.halt:
    cli
    hlt
    jmp .halt

boot_drive db 0
align 4
dap:
    db 0x10, 0
    dw 31
    dw 0x7E00
    dw 0
    dq 1
msg_fail db 'Spit Fire SF0: stage load failure', 0

times 510-($-$$) db 0
dw 0xAA55
