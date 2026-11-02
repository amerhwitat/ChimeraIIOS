BITS 64
section .text
global koronos_x86_64_load_gdt_tss

; void koronos_x86_64_load_gdt_tss(const gdtr *descriptor, uint16_t selector)
; SysV AMD64: RDI=GDTR, SI=TSS selector.
koronos_x86_64_load_gdt_tss:
    lgdt [rdi]
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    push qword 0x08
    lea rax, [rel .reload_cs]
    push rax
    retfq
.reload_cs:
    mov ax, si
    ltr ax
    ret
