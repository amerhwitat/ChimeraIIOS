#include "chimera/dma.h"
#include "chimera/frame_allocator.h"

namespace {
static bool is_power_of_two(size_t value) {
    return value != 0 && (value & (value - 1u)) == 0;
}
static void clear_buffer(koronos_dma_buffer *out) {
    out->physical_address = 0;
    out->virtual_address = 0;
    out->size = 0;
    out->page_count = 0;
}
}

extern "C" int koronos_dma_alloc(size_t size, size_t alignment, uint64_t dma_mask,
                                  koronos_dma_buffer *out) {
    if (!out) return -1;
    clear_buffer(out);
    if (!size || !is_power_of_two(alignment) ||
        alignment < KORONOS_FRAME_SIZE || alignment > 0x100000ull)
        return -1;
    if (size > SIZE_MAX - (size_t)(KORONOS_FRAME_SIZE - 1u)) return -1;
    const size_t pages_size = (size + (size_t)KORONOS_FRAME_SIZE - 1u) /
                              (size_t)KORONOS_FRAME_SIZE;
    if (!pages_size || pages_size > UINT32_MAX) return -1;
    const uint64_t alignment_pages = (uint64_t)alignment / KORONOS_FRAME_SIZE;
    if (pages_size > UINT32_MAX || alignment_pages == 0 ||
        pages_size + alignment_pages - 1u > UINT32_MAX) return -1;
    const uint32_t pages = (uint32_t)pages_size;
    const uint32_t reserve_pages = (uint32_t)(pages_size + alignment_pages - 1u);
    const uint64_t reserve_physical = koronos_frame_alloc_contiguous(reserve_pages);
    if (!reserve_physical) return -2;

    /* Over-allocate so larger-than-page alignments can be satisfied without
     * trusting the frame allocator to provide a particular alignment. Release
     * the unused prefix/suffix back to the same contiguous-frame allocator.
     */
    const uint64_t mask = (uint64_t)alignment - 1u;
    if (reserve_physical > UINT64_MAX - mask) {
        (void)koronos_frame_free_contiguous(reserve_physical, reserve_pages);
        return -3;
    }
    const uint64_t physical = (reserve_physical + mask) & ~mask;
    const uint64_t last = physical + (uint64_t)pages * KORONOS_FRAME_SIZE - 1u;
    const uint64_t reserve_end = reserve_physical +
        (uint64_t)reserve_pages * KORONOS_FRAME_SIZE;
    if (last < physical || physical < reserve_physical ||
        last >= reserve_end || last > dma_mask) {
        (void)koronos_frame_free_contiguous(reserve_physical, reserve_pages);
        return -3;
    }
    const uint32_t prefix_pages = (uint32_t)((physical - reserve_physical) /
                                              KORONOS_FRAME_SIZE);
    const uint32_t suffix_pages = reserve_pages - prefix_pages - pages;
    if (prefix_pages &&
        koronos_frame_free_contiguous(reserve_physical, prefix_pages) != 0) {
        (void)koronos_frame_free_contiguous(reserve_physical, reserve_pages);
        return -4;
    }
    if (suffix_pages &&
        koronos_frame_free_contiguous(physical + (uint64_t)pages * KORONOS_FRAME_SIZE,
                                      suffix_pages) != 0) {
        (void)koronos_frame_free_contiguous(physical, pages);
        return -4;
    }

    /* frame_allocator.h explicitly guarantees identity mapping for returned
     * frames in the bootstrap map. A future VM/MMIO layer must replace this
     * identity assumption before high-half-only mappings or IOMMU use.
     */
    out->physical_address = physical;
    out->virtual_address = (uintptr_t)physical;
    out->size = size;
    out->page_count = pages;
    uint8_t *bytes = (uint8_t *)out->virtual_address;
    for (size_t i = 0; i < pages_size * (size_t)KORONOS_FRAME_SIZE; ++i)
        bytes[i] = 0;
    return 0;
}

extern "C" int koronos_dma_free(koronos_dma_buffer *buffer) {
    if (!buffer || !buffer->physical_address || !buffer->page_count ||
        buffer->virtual_address != (uintptr_t)buffer->physical_address ||
        (buffer->physical_address & (KORONOS_FRAME_SIZE - 1u)) != 0)
        return -1;
    const int result = koronos_frame_free_contiguous(buffer->physical_address,
                                                      buffer->page_count);
    if (result == 0) clear_buffer(buffer);
    return result;
}
