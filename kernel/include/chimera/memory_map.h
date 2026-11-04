#ifndef CHIMERA_MEMORY_MAP_H
#define CHIMERA_MEMORY_MAP_H
#include <stdint.h>
#define CHM_PAGE_4K 0x1000ull
#define CHM_PAGE_2M 0x200000ull
#define CHM_PAGE_1G 0x40000000ull
typedef struct { uint64_t base, length; uint32_t type, attributes; } chm_phys_region_t;
#endif
