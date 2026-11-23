BITS 64

section .text

global koronos_context_trampoline
extern koronos_preempt_task_entry

; First-run entry for a preemptive kernel task. The crafted frame preloads RDI
; with the task pointer, so this trampoline remains correct even if a timer IRQ
; preempts it before the first CALL. The timer epilogue restores RDI from that
; task's own saved frame, not from the mutable global current-task pointer.
; After IRETQ, RSP == task stack top (16-byte aligned); CALL makes RSP % 16 == 8
; on entry to the SysV AMD64 C++ function.
koronos_context_trampoline:
    call koronos_preempt_task_entry
.trap:
    hlt
    jmp .trap
