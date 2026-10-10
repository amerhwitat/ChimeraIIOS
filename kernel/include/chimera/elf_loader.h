#pragma once
#include <stdint.h>
#include "process.h"
#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_ELF_PAGE_SIZE 4096u
#define CHIMERA_ELF_USER  1u
#define CHIMERA_ELF_WRITE 2u
#define CHIMERA_ELF_EXEC  4u
#define CHIMERA_ELF_STACK_PAGES 16u
#define CHIMERA_ELF_MAX_MAPPED_PAGES 272u

/*
 * Architecture/platform contract for a real loader backend:
 * - alloc_page returns a unique physical page and a writable kernel alias.
 * - map_user_page installs a user PTE with the exact requested R/W/NX policy.
 * - unmap_user_page removes the PTE and invalidates its TLB entry.
 * - free_page releases only pages allocated by this transaction.
 * - enter_user must install the kernel's valid user return frame and transfer
 *   to CPL3; it must not return on successful transfer.
 * The generic loader does not pretend to implement a physical allocator, page
 * tables, TSS, APIC, or IRETQ. Those must be provided by the architecture port.
 */
typedef struct chimera_elf_loader_ops {
    void *context;
    int (*alloc_page)(void *context, uint64_t *physical, void **writable_alias);
    int (*map_user_page)(void *context, uint64_t virtual_address,
                         uint64_t physical, uint32_t permissions);
    void (*unmap_user_page)(void *context, uint64_t virtual_address);
    void (*free_page)(void *context, uint64_t physical);
    int (*enter_user)(void *context, uint64_t entry, uint64_t stack_top,
                      uint32_t pid);
} chimera_elf_loader_ops;

/* Maps/copies an admitted ET_EXEC image transactionally, creates a zeroed
 * 64-KiB user stack with an unmapped guard page, and asks the backend to enter
 * ring 3. A returning enter_user callback is treated as a failed handoff and
 * triggers rollback. This is usable only with a fully implemented backend. */
int chimera_elf_load_and_enter(const void *image, uint64_t image_size,
                               uint16_t machine, uint64_t stack_top,
                               const chimera_elf_loader_ops *ops,
                               uint32_t *pid_out);

#ifdef __cplusplus
}
#endif
