#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_FRAME_SIZE 4096ull
#define KORONOS_FRAME_PHYS_LIMIT 0x100000000ull
/* Initialize from the Multiboot2 memory-map tag. Must run after module scan. */
int koronos_frame_allocator_init(uint64_t multiboot_info, uint64_t kernel_base, uint64_t kernel_end);
/* Returned physical addresses are identity-mapped by the bootstrap map. */
uint64_t koronos_frame_alloc(void);
uint64_t koronos_frame_alloc_contiguous(uint32_t page_count);
int koronos_frame_free(uint64_t physical_address);
int koronos_frame_free_contiguous(uint64_t physical_address, uint32_t page_count);
uint64_t koronos_frame_free_count(void);
/* VM-owned frame references. New allocations start with one reference. */
uint64_t koronos_vm_frame_alloc(void);
uint64_t koronos_vm_frame_alloc_contiguous(uint32_t page_count);
int koronos_vm_frame_retain(uint64_t physical_address);
int koronos_vm_frame_release(uint64_t physical_address);
int koronos_vm_frame_release_contiguous(uint64_t physical_address, uint32_t page_count);
uint32_t koronos_vm_frame_refcount(uint64_t physical_address);
#ifdef __cplusplus
}
#endif
