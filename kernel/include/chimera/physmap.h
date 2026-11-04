#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_PHYSMAP_LIMIT 0x100000000ull

/* Verifies the exact four-GiB, supervisor-only 2-MiB identity map installed
   by kernel/arch/x86_64/entry.asm. Must run on the bootstrap CPU in long mode. */
int koronos_physmap_init(void);
int koronos_physmap_validate_range(uint64_t physical, uint64_t length);
void *koronos_phys_to_virt(uint64_t physical, uint64_t length);
int koronos_physmap_ready(void);

#ifdef __cplusplus
}
#endif
