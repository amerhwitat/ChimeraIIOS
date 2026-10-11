#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_PHYSMEM_PAGE_SIZE 4096u
#define CHIMERA_PHYSMEM_LIMIT_BYTES 0x100000000ull
/* Bootstrap identity-map allocator: only manages page frames below 4 GiB,
 * which the current x86-64 entry.asm maps through 2-MiB identity PDEs. */
int chimera_physmem_init(uint64_t multiboot2_info, uint64_t kernel_base, uint64_t kernel_end);
int chimera_physmem_alloc_page(uint64_t *physical_address);
int chimera_physmem_free_page(uint64_t physical_address);
uint64_t chimera_physmem_free_pages(void);
uint64_t chimera_physmem_total_pages(void);
int chimera_physmem_ready(void);
#ifdef __cplusplus
}
#endif
