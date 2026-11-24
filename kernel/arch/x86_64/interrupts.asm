BITS 64

section .text
extern chimera_interrupt_dispatch
global chimera_interrupt_common
global chimera_isr_table
global koronos_preempt_yield

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
%elif v = 33
    jmp koronos_preempt_yield_common
%elif v = 49
    jmp koronos_ap_tick_common
%elif v = 50
    jmp koronos_ap_work_common
%else
    jmp chimera_interrupt_common
%endif
%assign v v+1
%endrep

extern koronos_preempt_irq_handler
extern koronos_preempt_current_ctx
extern koronos_user_timeout_irq
extern koronos_user_timeout_abort

; Vector 32 is both the relocatable PIT IRQ0 and the kernel timer-preemption
; gate. Kernel-mode entries save the full GPR set and may switch stacks before
; IRETQ; CPL3 entries retain the userspace timeout path below.
koronos_timer_irq_common:
    test qword [rsp + 16], 3          ; CPU-saved CS.RPL
    jnz koronos_timer_user_path
    mov rdi, 32
    jmp koronos_preempt_common

; x2APIC IPI vectors. Vector 49 is the PIT tick rebroadcast to APs, and 50 is
; work-dispatch. The C handler sends the local APIC EOI for both.
koronos_ap_tick_common:
    mov rdi, 49
    jmp koronos_preempt_common

koronos_ap_work_common:
    mov rdi, 50
    jmp koronos_preempt_common

; Software gate used by scheduler tasks to yield, block or exit. The IDT gate
; is a software interrupt, so it preserves the full preemptible frame and
; requires no PIC/APIC EOI.
global koronos_preempt_yield
koronos_preempt_yield:
    int 33
    ret

; Dedicated supervisor software gate used by a task to yield or exit. It uses
; the same save/switch/IRETQ epilogue but does not send a PIC EOI.
koronos_preempt_yield_common:
    mov rdi, 33
    jmp koronos_preempt_common

koronos_preempt_common:
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
    mov rbx, rsp
    and rsp, -16
    call koronos_preempt_irq_handler
    mov rsp, rbx
    test rax, rax
    jz koronos_preempt_restore
    ; FS:0 still names the outgoing context: the C handler selects a target but
    ; leaves the active-context pointer to this epilogue. Save the outgoing
    ; interrupt frame there before installing the selected context and CR3.
    mov rdx, [fs:0]
    test rdx, rdx
    jz .load_selected
    mov [rdx], rsp
.load_selected:
    mov r8, [rax]                         ; selected Context*
    mov r9, [rax + 8]                     ; selected CR3 (0 keeps current)
    mov [fs:0], r8
    mov rsp, [r8]
    test r9, r9
    jz koronos_preempt_restore
    mov cr3, r9
koronos_preempt_restore:
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
    add rsp, 8                        ; discard stub vector
    iretq

; IRQ0 is the only interrupt enabled while a userspace image runs. The TSS
; switches to RSP0 before this stub; swapgs establishes the kernel GS state.
; A timeout aborts the user continuation and returns to the saved kernel call
; frame instead of IRETQ'ing back into the expired user process.
koronos_timer_user_path:
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
