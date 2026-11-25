; SIPI-applied AP bootstrap stub for Koronos.
;
; The BSP copies this image to physical 0x7000 and patches the labelled fields.
; Absolute references are deliberately emitted as raw immediates/displacements
; so the same bytes execute correctly from the low SIPI page rather than from
; the kernel's higher-half link address.

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
global koronos_ap_trampoline_gdtr_ptr_patch
global koronos_ap_trampoline_lm_jump_patch
global koronos_ap_trampoline_lm_entry
global koronos_ap_trampoline_stack_imm
global koronos_ap_trampoline_state_imm
global koronos_ap_trampoline_tsc_lo_imm
global koronos_ap_trampoline_tsc_hi_imm

koronos_ap_trampoline_start:
    cli
    cld
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x6000

    ; LGDT [disp16] -- displacement is patched to the low-page GDTR offset.
    db 0x0F, 0x01, 0x16
koronos_ap_trampoline_gdtr_disp: dw 0

    ; PAE + CR3 + EFER.LME. PML4 physical address is patched by the BSP.
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

    ; 32-bit far jump: 66 EA offset32 selector16. Offset is patched.
    db 0x66, 0xEA
koronos_ap_trampoline_pm_jump_patch: dd 0
    dw 0x0008

BITS 32
koronos_ap_trampoline_pm_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax

    ; mov eax, moffs32; lgdt [eax]. moffs is the kernel GDT pointer address.
    db 0xA1
koronos_ap_trampoline_gdtr_ptr_patch: dd 0
    db 0x0F, 0x01, 0x18

    ; 64-bit far jump: EA offset32 selector16 into the kernel GDT.
    db 0xEA
koronos_ap_trampoline_lm_jump_patch: dd 0
    dw 0x0008

BITS 64
koronos_ap_trampoline_lm_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor ax, ax
    mov fs, ax
    mov gs, ax
    db 0x48, 0xBC
koronos_ap_trampoline_stack_imm: dq 0
    db 0x49, 0xBC
koronos_ap_trampoline_state_imm: dq 0

    ; Synchronize this core's TSC with the BSP's TSC so overlap timestamps are
    ; comparable. mov ecx, 0x10; mov eax, imm32; mov edx, imm32; wrmsr.
    db 0xB9
    dd 0x00000010
    db 0xB8
koronos_ap_trampoline_tsc_lo_imm: dd 0
    db 0xBA
koronos_ap_trampoline_tsc_hi_imm: dd 0
    db 0x0F, 0x30

    ; Publish AP identity and start timestamp, then acknowledge online state.
    mov eax, 1
    cpuid
    shr ebx, 24
    mov dword [r12 + 32], ebx
    rdtsc
    shl rdx, 32
    or rax, rdx
    mov qword [r12 + 48], rax
    mov dword [r12 + 0], 1
    mfence

.wait_go:
    cmp dword [r12 + 4], 0
    je .wait_go

    mov ecx, 1
.round:
.wait_bsp:
    cmp dword [r12 + 12], ecx
    jb .wait_bsp
    mov dword [r12 + 16], ecx
    mov dword [r12 + 20], ecx
    inc ecx
    cmp ecx, 256
    jbe .round

    rdtsc
    shl rdx, 32
    or rax, rdx
    mov qword [r12 + 64], rax

.stop:
    cmp dword [r12 + 8], 0
    je .stop
    mov dword [r12 + 80], 1
    hlt
    jmp .stop

align 16
koronos_ap_trampoline_gdtr:
    dw koronos_ap_trampoline_gdt_end - koronos_ap_trampoline_gdt - 1
koronos_ap_trampoline_gdt_base: dd 0
align 8
koronos_ap_trampoline_gdt:
    dq 0x0000000000000000
    dq 0x00CF9A000000FFFF          ; 32-bit flat code
    dq 0x00CF92000000FFFF          ; 32-bit flat data
koronos_ap_trampoline_gdt_end:
koronos_ap_trampoline_end:
