.code16
.global chimera_enter_protected
.global chimera_enter_long

# Legacy BIOS enters here in 16-bit real mode. The caller must provide a valid
# stack and boot context before calling. No BIOS interrupts are used after the handoff.
chimera_enter_protected:
    cli
    lgdt gdt32_ptr
    mov %cr0, %eax
    or $0x1, %eax
    mov %eax, %cr0
    ljmp $0x08, $protected_entry

.code32
protected_entry:
    mov $0x10, %ax
    mov %ax, %ds
    mov %ax, %es
    mov %ax, %ss
    ret

# Long-mode transition is a separate stage: enable PAE, load a validated page table,
# set EFER.LME, then set CR0.PG. Page-table construction is deliberately external.
chimera_enter_long:
    cli
    mov %cr4, %eax
    or $0x20, %eax
    mov %eax, %cr4
    mov %cr3, %eax
    # Caller has already placed the validated PML4 physical address in CR3.
    mov $0xC0000080, %ecx
    rdmsr
    or $0x100, %eax
    wrmsr
    mov %cr0, %eax
    or $0x80000000, %eax
    mov %eax, %cr0
    ljmp $0x08, $long_entry

.code64
long_entry:
    xor %ax, %ax
    mov %ax, %ds
    mov %ax, %es
    mov %ax, %ss
    ret

.align 8
gdt32:
    .quad 0x0000000000000000
    .quad 0x00CF9A000000FFFF
    .quad 0x00CF92000000FFFF
gdt32_ptr:
    .word gdt32_end-gdt32-1
    .long gdt32
gdt32_end:
