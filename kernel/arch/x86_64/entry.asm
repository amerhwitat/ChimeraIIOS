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
global _start

global __koronos_multiboot2_entry
__koronos_multiboot2_entry:
_start:
    cli
    cld
    mov esp, stack32_top
    cmp eax, MULTIBOOT2_BOOTLOADER_MAGIC
    jne .bad_boot
    mov [multiboot_magic], eax
    mov [multiboot_info], ebx

    ; Build the minimal identity paging structures needed to enter long mode.
    mov edi, page_table_base
    xor eax, eax
    mov ecx, 4096 / 4
    rep stosd

    ; Materialize relocatable table addresses before applying page flags.
    mov eax, pdpt_table
    or eax, 0x003
    mov [pml4_table], eax
    mov eax, pd_table
    or eax, 0x003
    mov [pdpt_table], eax
    mov dword [pd_table], 0x00000083
    mov dword [pd_table + 8], 0x00200083
    mov dword [pd_table + 16], 0x00400083
    mov dword [pd_table + 24], 0x00600083
    mov dword [pd_table + 32], 0x00800083
    mov dword [pd_table + 40], 0x00A00083
    mov dword [pd_table + 48], 0x00C00083
    mov dword [pd_table + 56], 0x00E00083
    mov dword [pd_table + 64], 0x01000083
    mov dword [pd_table + 72], 0x01200083
    mov dword [pd_table + 80], 0x01400083
    mov dword [pd_table + 88], 0x01600083
    mov dword [pd_table + 96], 0x01800083
    mov dword [pd_table + 104], 0x01A00083
    mov dword [pd_table + 112], 0x01C00083
    mov dword [pd_table + 120], 0x01E00083
    mov dword [pd_table + 128], 0x02000083
    mov dword [pd_table + 136], 0x02200083
    mov dword [pd_table + 144], 0x02400083
    mov dword [pd_table + 152], 0x02600083
    mov dword [pd_table + 160], 0x02800083
    mov dword [pd_table + 168], 0x02A00083
    mov dword [pd_table + 176], 0x02C00083
    mov dword [pd_table + 184], 0x02E00083
    mov dword [pd_table + 192], 0x03000083
    mov dword [pd_table + 200], 0x03200083
    mov dword [pd_table + 208], 0x03400083
    mov dword [pd_table + 216], 0x03600083
    mov dword [pd_table + 224], 0x03800083
    mov dword [pd_table + 232], 0x03A00083
    mov dword [pd_table + 240], 0x03C00083
    mov dword [pd_table + 248], 0x03E00083
    mov dword [pd_table + 256], 0x04000083
    mov dword [pd_table + 264], 0x04200083
    mov dword [pd_table + 272], 0x04400083
    mov dword [pd_table + 280], 0x04600083
    mov dword [pd_table + 288], 0x04800083
    mov dword [pd_table + 296], 0x04A00083
    mov dword [pd_table + 304], 0x04C00083
    mov dword [pd_table + 312], 0x04E00083
    mov dword [pd_table + 320], 0x05000083
    mov dword [pd_table + 328], 0x05200083
    mov dword [pd_table + 336], 0x05400083
    mov dword [pd_table + 344], 0x05600083
    mov dword [pd_table + 352], 0x05800083
    mov dword [pd_table + 360], 0x05A00083
    mov dword [pd_table + 368], 0x05C00083
    mov dword [pd_table + 376], 0x05E00083
    mov dword [pd_table + 384], 0x06000083
    mov dword [pd_table + 392], 0x06200083
    mov dword [pd_table + 400], 0x06400083
    mov dword [pd_table + 408], 0x06600083
    mov dword [pd_table + 416], 0x06800083
    mov dword [pd_table + 424], 0x06A00083
    mov dword [pd_table + 432], 0x06C00083
    mov dword [pd_table + 440], 0x06E00083
    mov dword [pd_table + 448], 0x07000083
    mov dword [pd_table + 456], 0x07200083
    mov dword [pd_table + 464], 0x07400083
    mov dword [pd_table + 472], 0x07600083
    mov dword [pd_table + 480], 0x07800083
    mov dword [pd_table + 488], 0x07A00083
    mov dword [pd_table + 496], 0x07C00083
    mov dword [pd_table + 504], 0x07E00083

    lgdt [gdt_ptr]
    mov eax, cr4
    or eax, 0x20
    mov cr4, eax
    mov eax, pml4_table
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
    jmp .hang32

BITS 64
long_mode_entry:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor ax, ax
    mov fs, ax
    mov gs, ax
    mov rsp, stack64_top
    mov r12, [multiboot_info]

    mov dword [boot_context + 0], KORONOS_BOOTINFO_MAGIC
    mov dword [boot_context + 4], KORONOS_ABI_VERSION
    mov qword [boot_context + 8], 0
    mov qword [boot_context + 8], r12
    mov qword [boot_context + 16], 0x100000
    lea rax, [rel __kernel_end]
    mov [boot_context + 24], rax
    mov qword [boot_context + 32], 0
    mov qword [boot_context + 40], 0
    mov dword [boot_context + 48], KORONOS_CPU_CISC
    mov dword [boot_context + 52], KORONOS_X86_LONG64
    mov qword [boot_context + 56], 0x3F8
    xor eax, eax
    mov [boot_context + 64], rax
    mov [boot_context + 72], rax
    mov [boot_context + 80], rax
    lea rdi, [rel boot_context]
    call koronos_boot

.hang64:
    cli
    hlt
    jmp .hang64

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
align 4096
page_table_base:
pml4_table: resb 4096
pdpt_table: resb 4096
pd_table: resb 4096
align 16
boot_context: resb 88
multiboot_magic: resd 1
multiboot_info: resq 1
align 16
stack32_bottom: resb 8192
stack32_top:
stack64_bottom: resb 16384
stack64_top:
__boot_bss_end:
