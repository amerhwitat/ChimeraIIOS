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

; int koronos_x86_64_context_switch(context *from, const context *to)
; context ABI: +0 saved RSP, +8 CR3 root.  Save/restore SysV callee-saved
; registers and switch CR3 before installing the target stack.
global koronos_x86_64_context_switch
koronos_x86_64_context_switch:
    test rdi, rdi
    jz .context_invalid
    test rsi, rsi
    jz .context_invalid
    cmp rdi, rsi
    je .context_same

    mov rax, [rsi]
    test rax, rax
    jz .context_invalid
    mov rcx, [rsi + 8]
    test rcx, rcx
    jz .context_invalid
    test rcx, 0xFFF
    jnz .context_invalid

    pushfq
    cli
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15

    mov rax, cr3
    mov [rdi + 8], rax
    mov [rdi], rsp

    cmp rax, rcx
    je .context_same_root
    mov cr3, rcx
.context_same_root:
    mov rsp, [rsi]
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    popfq
    xor eax, eax
    ret

.context_same:
    xor eax, eax
    ret
.context_invalid:
    mov eax, -1
    ret

; First-entry frame prepared by koronos_x86_64_context_prepare().
; R13 holds the entry point and R12 its argument.
global koronos_x86_64_context_trampoline
koronos_x86_64_context_trampoline:
    mov rdi, r12
    sub rsp, 8
    call r13
    add rsp, 8
    ud2
