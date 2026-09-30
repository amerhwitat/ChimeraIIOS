BITS 64

section .text
extern chimera_interrupt_dispatch
global chimera_interrupt_common
global chimera_isr_table

; Every vector has a dedicated entry point so the vector number is preserved.
; Exceptions which push a CPU error code are identified by vector in the common
; epilogue and the CPU-provided error code is removed before IRETQ.
%assign v 0
%rep 256
global chimera_isr_%+v
chimera_isr_%+v:
    push qword v
    jmp chimera_interrupt_common
%assign v v+1
%endrep

chimera_interrupt_common:
    push rax
    push rcx
    push rdx
    push rbx
    push rbp
    push rsi
    push rdi
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    push r14
    push r15

    mov rdi, [rsp + 120]
    mov rsi, rsp
    call chimera_interrupt_dispatch

    mov rax, [rsp + 120]
    cmp eax, 8
    je .error_code
    cmp eax, 10
    je .error_code
    cmp eax, 11
    je .error_code
    cmp eax, 12
    je .error_code
    cmp eax, 13
    je .error_code
    cmp eax, 14
    je .error_code
    cmp eax, 17
    je .error_code
    cmp eax, 21
    je .error_code
    cmp eax, 29
    je .error_code
    cmp eax, 30
    je .error_code

    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rbp
    pop rbx
    pop rdx
    pop rcx
    pop rax
    add rsp, 8
    iretq

.error_code:
    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rbp
    pop rbx
    pop rdx
    pop rcx
    pop rax
    add rsp, 16
    iretq

section .rodata
align 8
chimera_isr_table:
%assign v 0
%rep 256
    dq chimera_isr_%+v
%assign v v+1
%endrep
