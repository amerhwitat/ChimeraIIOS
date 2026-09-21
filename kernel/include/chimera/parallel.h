#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
uint32_t chimera_parallel_for(uint32_t begin,uint32_t end,uint32_t workers,void (*fn)(uint32_t,void*),void* arg);
#ifdef __cplusplus
}
#endif