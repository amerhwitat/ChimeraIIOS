#pragma once
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Kernel DMA allocation backed by contiguous physical frames.
 * The current bootstrap contract identity-maps allocated frames below 4 GiB.
 * This API does not provide IOMMU mappings or non-coherent cache maintenance.
 */
typedef struct koronos_dma_buffer {
    uint64_t physical_address;
    uintptr_t virtual_address;
    size_t size;
    uint32_t page_count;
} koronos_dma_buffer;

/* alignment must be a power of two and at least one page.
 * dma_mask is the largest bus address the device can address.
 * Returns 0 on success; failures leave out zeroed.
 */
int koronos_dma_alloc(size_t size, size_t alignment, uint64_t dma_mask,
                      koronos_dma_buffer *out);
int koronos_dma_free(koronos_dma_buffer *buffer);

#ifdef __cplusplus
}
#endif
