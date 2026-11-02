BITS 64

section .text
extern chimera_interrupt_dispatch
global chimera_interrupt_common
global chimera_isr_table

; Normalize every vector to one stack contract:
;   [GPRs r15..rax][vector][error][RIP][CS][RFLAGS][old RSP][old SS]
; The CPU supplies error for the architecturally-defined error-code vectors.
; All other stubs synthesize a zero error slot. RSP/SS are present only when
; the interrupted context was CPL3; the DPL0 gate keeps user entry disabled.
%assign v 0
%rep 256
global chimera_isr_%+v
chimera_isr_%+v:
%if v = 8 || v = 10 || v = 11 || v = 12 || v = 13 || v = 14 || v = 17 || v = 21 || v = 29 || v = 30
    push qword v
%else
    push qword 0
    push qword v
%endif
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

    ; chimera_x86_64_trap_frame: vector is byte offset 120.
    mov rdi, [rsp + 120]
    mov rsi, rsp
    ; Interrupts may arrive at any interrupted RSP alignment. Preserve the
    ; normalized frame in rsi and align the call stack for the SysV ABI.
    ; r12's interrupted value is already saved in the frame above.
    mov r12, rsp
    and rsp, -16
    call chimera_interrupt_dispatch
    mov rsp, r12

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
    ; Always discard normalized vector + error slots, including exceptions.
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
