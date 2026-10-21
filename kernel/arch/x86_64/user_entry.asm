BITS 64

section .text
global koronos_user_entry_init
global koronos_arch_enter_user
global koronos_syscall_entry
global koronos_user_timeout_abort
global koronos_user_timeout_abort_irq
extern koronos_syscall_user_dispatch
extern koronos_bootstrap_pml4
extern koronos_user_exit_code
extern koronos_target_log

%define USER_DATA 0x1B
%define USER_CODE 0x23
%define TSS_SELECTOR 0x28
%define EXIT_SENTINEL 0xFFFFFFFFFFFFFFF0

; Sets up a dedicated syscall stack and a 64-bit TSS. Kernel selectors retain
; their established values (CS=0x08, SS=0x10); ring 3 uses data=0x1B, code=0x23.
koronos_user_entry_init:
    pushfq
    push rbx
    cli

    ; Enable the architectural FP/SSE state required by baseline x86-64
    ; userspace. The freestanding kernel is built with -mno-sse and does not
    ; use SIMD while this single init process is active.
    mov rax, cr0
    and rax, ~(1 << 2)                     ; clear CR0.EM
    and rax, ~(1 << 3)                     ; clear CR0.TS
    or rax, (1 << 1)                       ; set CR0.MP
    mov cr0, rax
    mov rax, cr4
    or rax, (1 << 9) | (1 << 10)            ; CR4.OSFXSR | CR4.OSXMMEXCPT
    mov cr4, rax
    fninit
    ldmxcsr [rel koronos_default_mxcsr]

    lea rax, [rel koronos_syscall_stack_top]
    mov [rel koronos_tss64 + 4], rax       ; TSS.RSP0
    mov word [rel koronos_tss64 + 102], 104 ; I/O bitmap begins beyond TSS limit

    ; Encode the 16-byte available 64-bit TSS descriptor in GDT slots 5/6.
    lea rax, [rel koronos_tss64]
    mov rbx, rax
    and rbx, 0xFFFF
    shl rbx, 16
    or rbx, 103                             ; TSS limit = sizeof(TSS)-1
    mov rcx, rax
    shr rcx, 16
    and rcx, 0xFF
    shl rcx, 32
    or rbx, rcx
    mov rcx, rax
    shr rcx, 24
    and rcx, 0xFF
    shl rcx, 56
    or rbx, rcx
    mov rcx, 0x89
    shl rcx, 40
    or rbx, rcx
    mov [rel koronos_gdt64 + 40], rbx
    shr rax, 32
    mov [rel koronos_gdt64 + 48], rax

    lgdt [rel koronos_gdt64_ptr]
    mov ax, TSS_SELECTOR
    ltr ax

    ; Enable SYSCALL/SYSRET and keep interrupts, TF and DF masked in the kernel.
    mov ecx, 0xC0000080                    ; IA32_EFER
    rdmsr
    or eax, 0x801                          ; SCE + NXE (required by user PTEs)
    wrmsr
    mov ecx, 0xC0000081                    ; IA32_STAR
    mov rax, 0x0013000800000000             ; kernel CS=08; user base=13
    mov rdx, rax
    shr rdx, 32
    wrmsr
    mov ecx, 0xC0000082                    ; IA32_LSTAR
    lea rax, [rel koronos_syscall_entry]
    mov rdx, rax
    shr rdx, 32
    wrmsr
    mov ecx, 0xC0000084                    ; IA32_FMASK
    mov eax, 0x700                          ; mask TF, IF, DF on entry
    xor edx, edx
    wrmsr

    ; swapgs at syscall entry moves this per-CPU state into active GS.
    mov ecx, 0xC0000101                    ; IA32_GS_BASE
    xor eax, eax
    xor edx, edx
    wrmsr
    mov ecx, 0xC0000102                    ; IA32_KERNEL_GS_BASE
    lea rax, [rel koronos_cpu_syscall_state]
    mov rdx, rax
    shr rdx, 32
    wrmsr
    xor eax, eax
    pop rbx
    popfq
    ret

; int koronos_arch_enter_user(cr3, entry, user_stack_top)
; Kernel continuation is preserved on the original kernel stack. User code may
; return to it only by issuing the native exit syscall.
koronos_arch_enter_user:
    cmp rdi, 0
    je .bad_user_entry
    mov rax, 0x0000000100000000
    cmp rsi, rax
    jb .bad_user_entry
    mov rax, 0x0000800000000000
    cmp rsi, rax
    jae .bad_user_entry
    mov rax, 0x0000000100000000
    cmp rdx, rax
    jb .bad_user_entry
    mov rax, 0x0000800000000000
    cmp rdx, rax
    jae .bad_user_entry
    ; _start is compiled as a freestanding C function without a CRT shim:
    ; present the ABI function-entry alignment, RSP % 16 == 8.
    mov rax, rdx
    and rax, 0xF
    cmp rax, 8
    jne .bad_user_entry
    ; SYSCALL exit returns to this C caller, so preserve the callee-saved
    ; registers exactly as a normal ABI-conforming function must.
    push rbx
    push rbp
    push r12
    push r13
    push r14
    push r15
    pushfq
    pop rax
    mov [rel koronos_cpu_syscall_state + 40], rax
    cli
    mov [rel koronos_cpu_syscall_state + 16], rsp
    lea rax, [rel koronos_bootstrap_pml4]
    mov [rel koronos_cpu_syscall_state + 48], rax
    mov qword [rel koronos_user_exit_code], 0
    lea rax, [rel koronos_syscall_stack_top]
    mov [rel koronos_cpu_syscall_state + 0], rax
    mov [rel koronos_tss64 + 4], rax
    mov cr3, rdi
    push qword USER_DATA
    push rdx
    push qword 0x202                         ; enable IRQs in ring 3; IRQ0 enforces the in-kernel deadline
    push qword USER_CODE
    push rsi
    iretq
.bad_user_entry:
    mov eax, -1
    ret

; SYSCALL enters with RCX=user RIP and R11=user RFLAGS; it does not switch RSP.
koronos_syscall_entry:
    swapgs
    mov [gs:8], rsp
    mov rsp, [gs:0]
    push rax
    push rbx
    push rcx
    push rdx
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
    mov rdi, rsp
    sub rsp, 8
    call koronos_syscall_user_dispatch
    add rsp, 8
    ; Keep the syscall return value intact until the exit-sentinel check.
    mov rdx, EXIT_SENTINEL
    cmp rax, rdx
    je koronos_syscall_user_exit

    mov [gs:24], rax
    mov rcx, [rsp + 96]                     ; user RIP
    mov r11, [rsp + 32]                     ; user RFLAGS
    pop r15
    pop r14
    pop r13
    pop r12
    add rsp, 8                              ; saved r11
    pop r10
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rbp
    pop rdx
    add rsp, 8                              ; saved rcx
    pop rbx
    add rsp, 8                              ; saved rax; RAX becomes syscall result
    mov rax, [gs:24]
    ; Return through a privilege-changing IRETQ frame. This avoids depending
    ; on SYSRET selector arithmetic and keeps the user RSP off the kernel
    ; stack until the CPU performs the CPL0->CPL3 return.
    push qword USER_DATA
    push qword [gs:8]
    push r11
    push qword USER_CODE
    push rcx
    swapgs
    iretq

koronos_syscall_user_exit:
    lea rax, [rel koronos_bootstrap_pml4]
    mov cr3, rax
    mov rsp, [rel koronos_cpu_syscall_state + 16]
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    mov rax, [rel koronos_user_exit_code]
    push qword [rel koronos_cpu_syscall_state + 40]
    popfq
    swapgs
    ret

; Called only by the dedicated IRQ0 stub after the in-kernel deadline expires.
; Discard the interrupted user IRQ frame and resume the original C caller as a
; failed process, using the same saved kernel continuation as syscall exit.
koronos_user_timeout_abort_irq:
    lea rax, [rel koronos_bootstrap_pml4]
    mov cr3, rax
    mov rsp, [rel koronos_cpu_syscall_state + 16]
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    mov eax, -10
    push qword [rel koronos_cpu_syscall_state + 40]
    popfq
    ret

koronos_user_timeout_abort:
    lea rax, [rel koronos_bootstrap_pml4]
    mov cr3, rax
    mov rsp, [rel koronos_cpu_syscall_state + 16]
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    mov eax, -10
    push qword [rel koronos_cpu_syscall_state + 40]
    popfq
    swapgs
    ret

section .data
align 16
koronos_gdt64:
    dq 0x0000000000000000
    dq 0x00AF9A000000FFFF                    ; ring 0 long-mode code
    dq 0x00CF92000000FFFF                    ; ring 0 data
    dq 0x00CFF2000000FFFF                    ; ring 3 data
    dq 0x00AFFA000000FFFF                    ; ring 3 long-mode code
    dq 0, 0                                  ; available TSS descriptor, filled at init
koronos_gdt64_end:
koronos_gdt64_ptr:
    dw koronos_gdt64_end - koronos_gdt64 - 1
    dq koronos_gdt64

section .bss
alignb 16
koronos_cpu_syscall_state:
    resq 7                                   ; kernel_rsp0,user_rsp,saved_kernel_rsp,result,exit_code,rflags,kernel_cr3
alignb 16
koronos_tss64:
    resb 104
alignb 16
koronos_syscall_stack_bottom:
    resb 65536
koronos_syscall_stack_top:



section .rodata
align 4
koronos_default_mxcsr: dd 0x1F80
