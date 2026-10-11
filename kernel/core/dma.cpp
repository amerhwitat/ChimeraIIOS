#include "chimera/dma.h"
#include "chimera/physmem.h"
namespace { static bool valid(uint64_t b,uint64_t n,uint64_t m){return n && b<=UINT64_MAX-(n-1u) && b+n-1u<=m;} }
extern "C" int chimera_dma_device_init(chimera_dma_device*d,uint32_t bits,uint64_t mask,uint64_t coherent){
 if(!d||(bits!=32u&&bits!=64u)||!mask||!coherent)return -1;
 if(bits==32u&&(mask>0xffffffffull||coherent>0xffffffffull))return -2;
 if(coherent>mask)return -3;
 d->dma_mask=mask;d->coherent_mask=coherent;d->address_bits=bits;d->flags=0;return 0;
}
extern "C" int chimera_dma_map_physical(const chimera_dma_device*d,uint64_t p,uint64_t n,uint32_t dir,chimera_dma_mapping*m){
 if(!d||!m||!chimera_physmem_ready())return -1;
 if(dir<CHIMERA_DMA_TO_DEVICE||dir>CHIMERA_DMA_BIDIRECTIONAL)return -2;
 if((p&(CHIMERA_PHYSMEM_PAGE_SIZE-1u))||!valid(p,n,d->dma_mask))return -3;
 if(p>=CHIMERA_PHYSMEM_LIMIT_BYTES||n>CHIMERA_PHYSMEM_LIMIT_BYTES-p)return -4;
 /* Identity mapping only; no IOMMU or bounce buffering is implied. */
 m->physical_address=p;m->device_address=p;m->length=n;m->direction=dir;m->active=1;return 0;
}
extern "C" int chimera_dma_unmap(chimera_dma_mapping*m){if(!m||!m->active)return -1;m->active=0;m->device_address=0;m->length=0;return 0;}
extern "C" uint32_t chimera_dma_translate_nbit_width(uint32_t logical,uint32_t hardware){if(!logical||!hardware)return 0;return logical<hardware?logical:hardware;}
