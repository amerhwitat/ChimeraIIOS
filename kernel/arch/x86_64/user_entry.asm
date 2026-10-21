BITS 64
section .text
global koronos_x86_load_gdt_tss
global koronos_x86_enter_user_mode
; void koronos_x86_load_gdt_tss(const DescriptorPointer *gdtr, uint16_t selector)
koronos_x86_load_gdt_tss:
    lgdt [rdi]
    push qword 0x08
    lea rax, [rel .reload_segments]
    push rax
    retfq
.reload_segments:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor eax, eax
    mov fs, ax
    mov gs, ax
    mov ax, si
    ltr ax
    ret

; Non-returning CPL3 transition. Caller must have installed a valid IDT,
; syscall/interrupt return path, isolated address space and process-owned RSP0.
; rdi=ELF entry, rsi=top of user stack.
koronos_x86_enter_user_mode:
    cli
    mov rdx, rdi
    mov rcx, rsi
    mov ax, 0x1B
    mov ds, ax
    mov es, ax
    xor eax, eax
    mov fs, ax
    mov gs, ax
    push qword 0x1B
    push rcx
    push qword 0x202
    push qword 0x23
    push rdx
    iretq
