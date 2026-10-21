#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_X86_GDT_TSS_ABI 1u
#define CHIMERA_X86_KERNEL_CS 0x08u
#define CHIMERA_X86_KERNEL_DS 0x10u
#define CHIMERA_X86_USER_DS 0x1Bu
#define CHIMERA_X86_USER_CS 0x23u
#define CHIMERA_X86_TSS_SELECTOR 0x28u
typedef struct chimera_x86_tss64 {
 uint32_t reserved0; uint64_t rsp0,rsp1,rsp2; uint64_t reserved1;
 uint64_t ist1,ist2,ist3,ist4,ist5,ist6,ist7;
 uint64_t reserved2; uint16_t reserved3,iopb_offset;
} __attribute__((packed)) chimera_x86_tss64;
int chimera_x86_gdt_tss_prepare(uint64_t kernel_stack_top);
int chimera_x86_gdt_tss_install(uint64_t kernel_stack_top);
int chimera_x86_tss_set_kernel_stack(uint64_t kernel_stack_top);
const chimera_x86_tss64 *chimera_x86_tss_snapshot(void);
int chimera_x86_user_entry_available(void);
void koronos_x86_enter_user_mode(uint64_t entry,uint64_t user_stack_top);
#ifdef __cplusplus
}
#endif
