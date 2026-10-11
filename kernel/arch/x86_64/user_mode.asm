BITS 64
section .text
global chimera_x86_64_enter_user
; SysV AMD64: RDI=entry, RSI=user stack top. The TSS supplies RSP0 for
; exceptions/interrupts after the privilege transition. IF stays clear until
; a fully initialized interrupt/APIC timer path explicitly enables it.
chimera_x86_64_enter_user:
    cli
    mov rax, rdi
    mov rcx, rsi
    push qword 0x1B             ; ring-3 data selector
    push rcx                    ; user RSP
    push qword 0x2              ; reserved RFLAGS bit 1; interrupts disabled
    push qword 0x23             ; ring-3 code selector
    push rax                    ; user RIP
    iretq
.hang:
    cli
    hlt
    jmp .hang
