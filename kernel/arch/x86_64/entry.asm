BITS 32

%define MULTIBOOT2_MAGIC 0xE85250D6
%define MULTIBOOT2_BOOTLOADER_MAGIC 0x36D76289
%define KORONOS_ABI_VERSION 0x00010000
%define KORONOS_BOOTINFO_MAGIC 0x4B4F524F
%define KORONOS_CPU_CISC 1
%define KORONOS_X86_LONG64 2

section .multiboot2
align 8
mb2_header:
    dd MULTIBOOT2_MAGIC
    dd 0
    dd mb2_header_end - mb2_header
    dd -(MULTIBOOT2_MAGIC + 0 + (mb2_header_end - mb2_header))
    dw 0
    dw 0
    dd 8
mb2_header_end:

section .text.boot
extern koronos_boot
extern koronos_idle_loop
extern __kernel_end
global _start

global __koronos_multiboot2_entry
__koronos_multiboot2_entry:
_start:
    cli
    cld
    lea esp, [stack32_top]
    cmp eax, MULTIBOOT2_BOOTLOADER_MAGIC
    jne .bad_boot
    mov [multiboot_magic], eax
    mov dword [multiboot_info], ebx
    mov dword [multiboot_info + 4], 0

    ; Build the minimal identity paging structures needed to enter long mode.
    mov edi, page_table_base
    xor eax, eax
    mov ecx, 4096 / 4
    rep stosd

    ; Materialize relocatable table addresses before applying page flags.
    lea eax, [pdpt_table]
    or eax, 0x003
    mov [pml4_table], eax
    lea eax, [pd_table]
    or eax, 0x003
    mov [pdpt_table], eax
    ; Populate 512 2 MiB PDEs at runtime.  The page-table storage is BSS,
    ; so it must not contain assembler-time initializers.
    lea edi, [pd_table]
    mov eax, 0x00000083
    mov ecx, 512
.fill_pd:
    mov [edi], eax
    add eax, 0x00200000
    add edi, 8
    loop .fill_pd

    lgdt [gdt_ptr]
    mov eax, cr4
    or eax, 0x20
    mov cr4, eax
    lea eax, [pml4_table]
    mov cr3, eax
    mov ecx, 0xC0000080
    rdmsr
    or eax, 0x100
    wrmsr
    mov eax, cr0
    or eax, 0x80000001
    mov cr0, eax
    jmp 0x08:long_mode_entry

.bad_boot:
    cli
.hang32:
    hlt
    jmp near .hang32

BITS 64
long_mode_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor ax, ax
    mov fs, ax
    mov gs, ax
    lea rsp, [rel stack64_top]
    mov r12, [rel multiboot_info]

    mov dword [rel boot_context + 0], KORONOS_BOOTINFO_MAGIC
    mov dword [rel boot_context + 4], KORONOS_ABI_VERSION
    mov qword [rel boot_context + 8], r12
    mov qword [rel boot_context + 16], 0x100000
    lea rax, [rel __kernel_end]
    mov [rel boot_context + 24], rax
    mov qword [rel boot_context + 32], 0
    mov qword [rel boot_context + 40], 0
    mov dword [rel boot_context + 48], KORONOS_CPU_CISC
    mov dword [rel boot_context + 52], KORONOS_X86_LONG64
    mov qword [rel boot_context + 56], 0x3F8
    xor eax, eax
    mov dword [rel boot_context + 64], 0
    mov dword [rel boot_context + 68], 0
    mov [rel boot_context + 72], rax
    mov [rel boot_context + 80], rax
    lea rdi, [rel boot_context]
    call koronos_boot
    ; Keep the bootstrap vCPU executing after kernel initialization.  The old
    ; CLI/HLT loop made VMware report the vCPU as inactive/disabled.
    call koronos_idle_loop

.hang64:
    jmp near .hang64

section .rodata
align 8
gdt64:
    dq 0x0000000000000000
    dq 0x00AF9A000000FFFF
    dq 0x00AF92000000FFFF
gdt_ptr:
    dw gdt64_end - gdt64 - 1
    dq gdt64
gdt64_end:

section .bss
alignb 4096
page_table_base:
pml4_table: resb 4096
pdpt_table: resb 4096
pd_table: resb 4096
alignb 16
boot_context: resb 88
multiboot_magic: resd 1
multiboot_info: resq 1
alignb 16
stack32_bottom: resb 8192
stack32_top:
alignb 16
stack64_bottom: resb 16384
stack64_top:
__boot_bss_end:
