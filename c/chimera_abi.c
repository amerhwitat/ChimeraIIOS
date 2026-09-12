#include <stdint.h>
#include <stddef.h>

/* Stable C boundary used by kernel, boot and C++ service layers. */
uint64_t chimera_u64_mask(unsigned width) {
    if (width == 0) return 0;
    if (width >= 64) return UINT64_MAX;
    return (UINT64_C(1) << width) - UINT64_C(1);
}

void chimera_memzero(void* dst, size_t size) {
    unsigned char* p = (unsigned char*)dst;
    for (size_t i = 0; i < size; ++i) p[i] = 0;
}
