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
%if v = 32
    jmp koronos_timer_irq_common
%else
    jmp chimera_interrupt_common
%endif
%assign v v+1
%endrep

; IRQ0 is the only interrupt enabled while a userspace image runs. The TSS
; switches to RSP0 before this stub; swapgs establishes the kernel GS state.
; A timeout aborts the user continuation and returns to the saved kernel call
; frame instead of IRETQ'ing back into the expired user process.
extern koronos_user_timeout_irq
extern koronos_user_timeout_abort
koronos_timer_irq_common:
    swapgs
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
    sub rsp, 8
    call koronos_user_timeout_irq
    add rsp, 8
    test eax, eax
    jnz koronos_user_timeout_abort
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
    swapgs
    iretq

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
    ; A CPL3 interrupt pushes SS/RSP/RFLAGS/CS/RIP before the stub saves
    ; registers, so this frame is not guaranteed to satisfy the SysV AMD64
    ; pre-call 16-byte stack alignment. Preserve the frame pointer in RBX
    ; (its interrupted value is already saved in the frame), align for C, and
    ; restore the exact frame pointer before the common register epilogue.
    mov rbx, rsp
    and rsp, -16
    call chimera_interrupt_dispatch
    mov rsp, rbx

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
