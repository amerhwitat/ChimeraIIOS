[BITS 16]
[ORG 0x7E00]
%define CODE_SEL 0x08
%define DATA_SEL 0x10

start:
    cli
    call enable_a20
    lgdt [gdt_descriptor]
    mov eax, cr0
    or eax, 1
    mov cr0, eax
    jmp CODE_SEL:protected_mode

enable_a20:
    in al, 0x92
    or al, 2
    out 0x92, al
    ret

[BITS 32]
protected_mode:
    mov ax, DATA_SEL
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov esp, 0x9FC00
    mov eax, cr4
    or eax, (1 << 5) | (1 << 7)
    mov cr4, eax
    mov eax, 0x9000
    mov cr3, eax
    mov ecx, 0xC0000080
    rdmsr
    or eax, (1 << 8)
    wrmsr
    mov eax, cr0
    or eax, (1 << 31)
    mov cr0, eax
    jmp 0x18:long_mode_entry

align 8
gdt:
    dq 0
    dq 0x00AF9A000000FFFF
    dq 0x00AF92000000FFFF
    dq 0x00AF9A000000FFFF
gdt_descriptor:
    dw gdt_descriptor-gdt-1
    dd gdt

[BITS 64]
long_mode_entry:
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    extern sf2_entry_asm
    call sf2_entry_asm
.hang:
    hlt
    jmp .hang
