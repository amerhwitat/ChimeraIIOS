#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* N-bit logical addresses are never truncated into hardware DMA addresses. */
typedef struct chimera_dma_device { uint64_t dma_mask; uint64_t coherent_mask; uint32_t address_bits; uint32_t flags; } chimera_dma_device;
typedef struct chimera_dma_mapping { uint64_t physical_address; uint64_t device_address; uint64_t length; uint32_t direction; uint32_t active; } chimera_dma_mapping;
enum { CHIMERA_DMA_TO_DEVICE=1, CHIMERA_DMA_FROM_DEVICE=2, CHIMERA_DMA_BIDIRECTIONAL=3 };
int chimera_dma_device_init(chimera_dma_device*,uint32_t,uint64_t,uint64_t);
int chimera_dma_map_physical(const chimera_dma_device*,uint64_t,uint64_t,uint32_t,chimera_dma_mapping*);
int chimera_dma_unmap(chimera_dma_mapping*);
uint32_t chimera_dma_translate_nbit_width(uint32_t,uint32_t);
#ifdef __cplusplus
}
#endif
