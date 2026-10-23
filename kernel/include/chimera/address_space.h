#pragma once
#include <stdint.h>
#include "chimera/process_loader.h"

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_USER_VIRTUAL_MIN 0x0000000100000000ull
#define KORONOS_ADDRESS_SPACE_ABI 1u
#define KORONOS_VMA_ABI 1u
#define KORONOS_VMA_MAX 64u

enum koronos_vma_backing_kind { KORONOS_VMA_ANONYMOUS=0, KORONOS_VMA_ELF_IMAGE=1, KORONOS_VMA_FILE=2, KORONOS_VMA_SWAP=3 };
enum koronos_vma_residency { KORONOS_VMA_RESIDENT=1, KORONOS_VMA_PARTIAL=2, KORONOS_VMA_NONRESIDENT=3 };
typedef struct koronos_vma_descriptor {
    uint32_t abi;
    uint32_t backing_kind;
    uint32_t elf_flags;
    uint32_t residency;
    uint64_t virtual_base;
    uint64_t length;
    uint64_t backing_object;
    uint64_t backing_offset;
    uint64_t page_count;
    uint64_t resident_pages;
} koronos_vma_descriptor;

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
int koronos_address_space_vma_query(void *address_space, uint64_t virtual_address,
                                    koronos_vma_descriptor *out);
int koronos_address_space_vma_set_backing(void *address_space, uint64_t virtual_base,
                                          uint64_t length, uint32_t backing_kind,
                                          uint64_t backing_object, uint64_t backing_offset);
int koronos_address_space_evict_one(void *address_space);
/* Interrupt-safe probe never performs storage I/O. */
int koronos_address_space_page_fault_fastpath(void *address_space, uint64_t fault_address,
                                               uint64_t error_code);
/* Blocking resolver for a future pager thread; never call from IRQ/syscall entry. */
int koronos_address_space_handle_page_fault(void *address_space, uint64_t fault_address,
                                             uint64_t error_code);
int koronos_address_space_pin(void *address_space, uint64_t virtual_address, uint64_t length,
                              uint32_t write_access);
int koronos_address_space_unpin(void *address_space, uint64_t virtual_address, uint64_t length);
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
