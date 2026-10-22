#include "chimera/parallel.h"

// This API is deliberately single-worker until AP startup and independent CPU
// dispatch exist. A multi-worker request must not run serially and look like SMP.
uint32_t chimera_parallel_for(uint32_t begin, uint32_t end, uint32_t workers,
                              void (*fn)(uint32_t, void*), void* arg) {
    if (!fn || end <= begin) return 0;
    const uint32_t count = end - begin;
    if (workers == 0) workers = 1;
    if (workers > count) workers = count;
    if (workers > 1) return 0; // fail closed: no work was dispatched
    for (uint32_t i = begin; i < end; ++i) fn(i, arg);
    return count;
}
