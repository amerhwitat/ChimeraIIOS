#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// Executes serially only when the effective worker count is one. Returns zero
// without invoking the callback if more than one worker is requested; genuine
// AP-backed concurrent dispatch is not implemented yet.
uint32_t chimera_parallel_for(uint32_t begin, uint32_t end, uint32_t workers, void (*fn)(uint32_t, void*), void* arg);
#ifdef __cplusplus
}
#endif
