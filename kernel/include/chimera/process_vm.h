#pragma once
#include <stdint.h>
#include <stddef.h>
#include "process_loader.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_X86_VM_ABI 1u
#define CHIMERA_X86_VM_PAGE_SIZE 4096ull
#define CHIMERA_X86_VM_MAX_REGIONS 32u
#define CHIMERA_X86_VM_MAX_TABLES 512u
#define CHIMERA_X86_PTE_PRESENT (1ull<<0)
#define CHIMERA_X86_PTE_WRITABLE (1ull<<1)
#define CHIMERA_X86_PTE_USER (1ull<<2)
#define CHIMERA_X86_PTE_HUGE (1ull<<7)
#define CHIMERA_X86_PTE_NX (1ull<<63)
typedef struct chimera_x86_vm_ops {
 int (*alloc_pages)(void *context,uint32_t count,uint64_t *physical,void **kernel_alias);
 void (*free_pages)(void *context,uint64_t physical,uint32_t count);
 void *(*physical_to_virtual)(void *context,uint64_t physical);
 uint64_t boot_pml4_physical;
 uint32_t nx_enabled;
} chimera_x86_vm_ops;
typedef struct chimera_x86_address_space chimera_x86_address_space;
int chimera_x86_vm_init(const chimera_x86_vm_ops *ops,void *context);
chimera_x86_address_space *chimera_x86_vm_create(void);
int chimera_x86_vm_map(chimera_x86_address_space *space,uint64_t virtual_base,uint64_t size,uint32_t elf_flags,void **kernel_alias);
void chimera_x86_vm_destroy(chimera_x86_address_space *space);
uint64_t chimera_x86_vm_pml4_physical(const chimera_x86_address_space *space);
int chimera_x86_vm_make_loader_ops(chimera_elf_load_ops *out);
#ifdef __cplusplus
}
#endif
