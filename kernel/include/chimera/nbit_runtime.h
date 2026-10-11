#pragma once
#include <stdint.h>

/* Little-endian, caller-owned, fixed-capacity integer storage. No heap, exceptions,
   RTTI, or hidden allocation; width is arbitrary within the supplied capacity. */
struct ChimeraNBitConstView {
    const uint8_t *bytes;
    uint32_t bit_width;
    uint32_t capacity_bytes;
};
struct ChimeraNBitView {
    uint8_t *bytes;
    uint32_t bit_width;
    uint32_t capacity_bytes;
};

class ChimeraNBitArithmetic final {
public:
    static int validate(const ChimeraNBitConstView &value);
    static int add(ChimeraNBitView dst, ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
    static int subtract(ChimeraNBitView dst, ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
    static int bit_and(ChimeraNBitView dst, ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
    static int bit_or(ChimeraNBitView dst, ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
    static int bit_xor(ChimeraNBitView dst, ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
    static int bit_not(ChimeraNBitView dst, ChimeraNBitConstView src);
    static int shift_left(ChimeraNBitView dst, ChimeraNBitConstView src, uint32_t amount);
    static int shift_right(ChimeraNBitView dst, ChimeraNBitConstView src, uint32_t amount);
    static int compare_unsigned(ChimeraNBitConstView lhs, ChimeraNBitConstView rhs);
private:
    static void mask_top(ChimeraNBitView value);
};

extern "C" {
int chimera_nbit_word_add(uint8_t *dst, uint32_t dst_capacity, const uint8_t *lhs,
                          uint32_t lhs_capacity, const uint8_t *rhs, uint32_t rhs_capacity,
                          uint32_t bit_width);
int chimera_nbit_word_subtract(uint8_t *dst, uint32_t dst_capacity, const uint8_t *lhs,
                               uint32_t lhs_capacity, const uint8_t *rhs, uint32_t rhs_capacity,
                               uint32_t bit_width);
/* Reentrant batch API. Callers may dispatch disjoint [first, first+count) ranges
   to separate CPUs; each element is an independent fixed-width operation. */
int chimera_nbit_batch_add(uint8_t *dst, uint32_t dst_capacity,
                           const uint8_t *lhs, uint32_t lhs_capacity,
                           const uint8_t *rhs, uint32_t rhs_capacity,
                           uint32_t bit_width, uint32_t stride_bytes,
                           uint32_t first, uint32_t count);
}
