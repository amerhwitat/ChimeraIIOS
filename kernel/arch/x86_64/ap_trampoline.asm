; SIPI-applied AP bootstrap stub for Koronos.
;
; The BSP copies this image to physical 0x7000 and patches the labelled fields.
; Absolute references are emitted as raw immediates so the same bytes execute
; from the low SIPI page rather than from the kernel's link address. The AP
; enters the per-CPU C runtime and stays in the scheduler loop; it is not
; parked after a synthetic handshake.

BITS 16
section .text.ap

global koronos_ap_trampoline_start
global koronos_ap_trampoline_end
global koronos_ap_trampoline_gdtr
global koronos_ap_trampoline_gdt
global koronos_ap_trampoline_gdtr_disp
global koronos_ap_trampoline_gdt_base
global koronos_ap_trampoline_pml4_patch
global koronos_ap_trampoline_pm_jump_patch
global koronos_ap_trampoline_pm_entry
global koronos_ap_trampoline_lm_jump_patch
global koronos_ap_trampoline_lm_entry
global koronos_ap_trampoline_stack_base_imm
global koronos_ap_trampoline_state_imm
global koronos_ap_trampoline_entry_imm

koronos_ap_trampoline_start:
    cli
    cld
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x6000

    db 0x0F, 0x01, 0x16
koronos_ap_trampoline_gdtr_disp: dw 0

    mov eax, cr4
    or eax, 0x20
    mov cr4, eax
    db 0x66, 0xB8
koronos_ap_trampoline_pml4_patch: dd 0
    mov cr3, eax
    mov ecx, 0xC0000080
    rdmsr
    or eax, 0x100
    wrmsr
    mov eax, cr0
    or eax, 0x80000001
    mov cr0, eax

    db 0x66, 0xEA
koronos_ap_trampoline_pm_jump_patch: dd 0
    dw 0x0008

BITS 32
koronos_ap_trampoline_pm_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax

    ; Far jump to long mode using the low-page GDT's 64-bit code descriptor.
    db 0xEA
koronos_ap_trampoline_lm_jump_patch: dd 0
    dw 0x0018

BITS 64
koronos_ap_trampoline_lm_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor ax, ax
    mov fs, ax
    mov gs, ax

    ; The BSP patches this core's private stack top into r11 before SIPI.
    db 0x49, 0xBB
koronos_ap_trampoline_stack_base_imm: dq 0   ; mov r11, stack_top
    mov rsp, r11

    xor edi, edi                              ; APIC ID detected in C
    db 0x48, 0xBE
koronos_ap_trampoline_state_imm: dq 0         ; mov rsi, shared state
    db 0x48, 0xB8
koronos_ap_trampoline_entry_imm: dq 0         ; mov rax, koronos_ap_cpu_entry
    call rax
.halt:
    hlt
    jmp .halt

align 16
koronos_ap_trampoline_gdtr:
    dw koronos_ap_trampoline_gdt_end - koronos_ap_trampoline_gdt - 1
koronos_ap_trampoline_gdt_base: dd 0
align 8
koronos_ap_trampoline_gdt:
    dq 0x0000000000000000
    dq 0x00CF9A000000FFFF          ; selector 0x08: 32-bit flat code
    dq 0x00CF92000000FFFF          ; selector 0x10: flat data
    dq 0x00AF9A000000FFFF          ; selector 0x18: 64-bit flat code
koronos_ap_trampoline_gdt_end:
koronos_ap_trampoline_end:
