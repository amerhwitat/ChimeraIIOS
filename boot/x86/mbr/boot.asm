; Chimera II OS x86 MBR research stub
; Production boot flow targets UEFI/GPT. This compatibility stub is retained for research.
BITS 16
ORG 0x7C00
start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti
    mov si, message
.print:
    lodsb
    test al, al
    jz .hang
    mov ah, 0x0E
    int 0x10
    jmp .print
.hang:
    cli
    hlt
    jmp .hang
message db 'Chimera II Spit Fire MBR research stub', 0
TIMES 510-($-$$) DB 0
DW 0xAA55
