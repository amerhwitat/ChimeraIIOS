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

; int koronos_x86_64_context_switch_raw(context *from, const context *to)
; The C wrapper validates BSP ownership and performs the paired TSS.RSP0/PID
; handoff with interrupts disabled. This primitive only exchanges stack frames.
; It deliberately refuses a different CR3 until TLB shootdown support exists.
global koronos_x86_64_context_switch_raw
koronos_x86_64_context_switch_raw:
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
    mov rdx, cr3
    cmp rcx, rdx
    jne .context_space_mismatch

    pushfq
    cli
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15

    ; The wrapper stored the outgoing CR3 before changing CR3.
    mov [rdi], rsp
    mov rsp, rax
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
.context_space_mismatch:
    mov eax, -2
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
