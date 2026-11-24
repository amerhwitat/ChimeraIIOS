BITS 64

section .text

global koronos_context_trampoline
global koronos_arch_set_fs_base
global koronos_arch_cpu_state_init
global koronos_arch_cpu_state_table
extern chimera_sched_task_entry
extern koronos_syscall_entry

%define CPU_STATE_STRIDE 1024
%define CPU_STATE_SLOTS 256
%define GDT_PTR_OFF 256
%define TSS_OFF 320
%define SYSCALL_STATE_OFF 512
%define TSS_SELECTOR 0x28

; First-run entry for a scheduler task. The crafted IRETQ frame preloads RDI
; with the task pointer; the timer epilogue restores RDI from that task's own
; saved frame rather than the mutable per-CPU current pointer.
koronos_context_trampoline:
    call chimera_sched_task_entry
.trap:
    hlt
    jmp .trap

; FS base is per-core and does not collide with the kernel GS state used by
; SYSCALL/SYSRET. The scheduler's CpuState begins with the active Context*.
koronos_arch_set_fs_base:
    mov ecx, 0xC0000100                  ; IA32_FS_BASE
    mov eax, edi
    shr rdi, 32
    mov edx, edi
    wrmsr
    xor eax, eax
    ret

; Builds an independent GDT/TSS and syscall-state slot for one CPU.
; rdi = cpu index, rsi = kernel stack top for TSS.RSP0.
koronos_arch_cpu_state_init:
    cmp rdi, CPU_STATE_SLOTS - 1
    ja .bad
    mov eax, CPU_STATE_STRIDE
    mul rdi                               ; rax = cpu * stride
    lea r8, [rel koronos_arch_cpu_state_table]
    add r8, rax

    mov rdi, r8
    mov ecx, CPU_STATE_STRIDE / 8
    xor eax, eax
    rep stosq

    mov rax, 0x00AF9A000000FFFF           ; ring 0 long-mode code
    mov [r8 + 8], rax
    mov rax, 0x00CF92000000FFFF            ; ring 0 data
    mov [r8 + 16], rax
    mov rax, 0x00CFF2000000FFFF            ; ring 3 data
    mov [r8 + 24], rax
    mov rax, 0x00AFFA000000FFFF            ; ring 3 long-mode code
    mov [r8 + 32], rax

    lea r9, [r8 + TSS_OFF]
    mov [r9 + 4], rsi                      ; TSS.RSP0
    mov word [r9 + 102], 104               ; I/O bitmap beyond TSS limit

    ; Available 64-bit TSS descriptor in GDT slots 5/6.
    mov r10, r9
    and r10, 0xFFFF
    shl r10, 16
    or r10, 103                            ; TSS limit
    mov rax, r9
    shr rax, 16
    and rax, 0xFF
    shl rax, 32
    or r10, rax
    mov rax, r9
    shr rax, 24
    and rax, 0xFF
    shl rax, 56
    or r10, rax
    mov rax, 0x89
    shl rax, 40
    or r10, rax
    mov [r8 + 40], r10
    shr r9, 32
    mov [r8 + 48], r9d

    mov word [r8 + GDT_PTR_OFF], 55         ; 7 GDT entries
    mov [r8 + GDT_PTR_OFF + 2], r8
    lgdt [r8 + GDT_PTR_OFF]
    mov ax, TSS_SELECTOR
    ltr ax

    ; Reload CS from the new per-CPU GDT. An AP enters with selector 0x18 from
    ; the low SIPI GDT, which is not a code descriptor in this table; without
    ; the reload the first IRETQ faults with #GP(0x18).
    mov rax, .cs_reloaded
    push qword 0x08
    push rax
    retfq
.cs_reloaded:

    ; Enable the baseline FP/SSE state and native SYSCALL entry on this CPU.
    mov rax, cr0
    and rax, 0FFFFFFFFFFFFFFFBh
    and rax, 0FFFFFFFFFFFFFFF7h
    or rax, 2
    mov cr0, rax
    mov rax, cr4
    or rax, (1 << 9) | (1 << 10)
    mov cr4, rax
    fninit

    mov ecx, 0xC0000080                   ; IA32_EFER
    rdmsr
    or eax, 1
    wrmsr
    mov ecx, 0xC0000081                   ; IA32_STAR
    xor eax, eax
    mov edx, 0x00130008
    wrmsr
    mov ecx, 0xC0000082                   ; IA32_LSTAR
    lea rax, [rel koronos_syscall_entry]
    mov rdx, rax
    shr rdx, 32
    wrmsr
    mov ecx, 0xC0000084                   ; IA32_FMASK
    mov eax, 0x700
    xor edx, edx
    wrmsr
    mov ecx, 0xC0000101                   ; IA32_GS_BASE
    xor eax, eax
    xor edx, edx
    wrmsr
    mov ecx, 0xC0000102                   ; IA32_KERNEL_GS_BASE
    lea rax, [r8 + SYSCALL_STATE_OFF]
    mov rdx, rax
    shr rdx, 32
    wrmsr
    xor eax, eax
    ret
.bad:
    mov eax, -1
    ret

section .bss
alignb 16
koronos_arch_cpu_state_table:
    resb CPU_STATE_SLOTS * CPU_STATE_STRIDE
