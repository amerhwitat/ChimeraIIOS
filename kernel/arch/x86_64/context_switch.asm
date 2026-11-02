BITS 64
section .text
global koronos_context_switch
global koronos_scheduler_task_trampoline
extern chimera_sched_task_start

; void koronos_context_switch(uint64_t *old_rsp, uint64_t new_rsp)
; Save the SysV callee-saved register set and RFLAGS. Each task owns its stack.
koronos_context_switch:
    pushfq
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov [rdi], rsp
    mov rsp, rsi
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    popfq
    ret

; A new task's initial frame restores its stable slot index into R12.
; Enter the C dispatcher with the standard SysV stack alignment.
koronos_scheduler_task_trampoline:
    mov edi, r12d
    sub rsp, 8
    call chimera_sched_task_start
    ud2
