#pragma once
#include <stdint.h>
#include "chimera/process_loader.h"

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_USER_VIRTUAL_MIN 0x0000000100000000ull
#define KORONOS_ADDRESS_SPACE_ABI 1u

/* Enables the process address-space backend after the physical allocator and
   CPU feature discovery have completed. Fails closed if NX is unavailable. */
typedef void (*koronos_tlb_shootdown_fn)(uint64_t root_physical, uint64_t virtual_base,
                                         uint64_t length, void *context);
/* Callback contract: synchronously invalidate the requested range on every CPU
   that may use this root and return only after all acknowledgements arrive.
   Mapping mutation/reclamation remains disabled until a real callback is installed. */
int koronos_address_space_register_tlb_shootdown(koronos_tlb_shootdown_fn callback,
                                                  void *context);
int koronos_address_space_map(void *address_space, uint64_t virtual_base, uint64_t length,
                              uint32_t elf_flags);
int koronos_address_space_unmap(void *address_space, uint64_t virtual_base, uint64_t length);
int koronos_address_space_protect(void *address_space, uint64_t virtual_base, uint64_t length,
                                  uint32_t elf_flags);
int koronos_address_space_query(void *address_space, uint64_t virtual_address,
                                uint64_t *physical_address, uint32_t *elf_flags);
int koronos_address_space_init(void);
int koronos_address_space_ready(void);
int koronos_address_space_self_test(void);
const chimera_elf_load_ops *koronos_address_space_loader_ops(void);
uint64_t koronos_address_space_root(const void *address_space);
int koronos_address_space_validate_user_range(uint64_t root_physical, uint64_t address,
                                              uint64_t length, uint32_t write_access);
uint64_t koronos_address_space_count(void);

#ifdef __cplusplus
}
#endif
