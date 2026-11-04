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
int koronos_address_space_init(void);
int koronos_address_space_ready(void);
int koronos_address_space_self_test(void);
const chimera_elf_load_ops *koronos_address_space_loader_ops(void);
uint64_t koronos_address_space_root(const void *address_space);
int koronos_address_space_validate_user_range(uint64_t root_physical, uint64_t address,
                                              uint64_t length, uint32_t write_access);
/* Bounded current-address-space copies; validate every covered user page first. */
int koronos_copy_from_user(void *kernel_destination, uint64_t user_source, uint64_t length);
int koronos_copy_to_user(uint64_t user_destination, const void *kernel_source, uint64_t length);
uint64_t koronos_address_space_count(void);

#ifdef __cplusplus
}
#endif
