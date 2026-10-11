#pragma once
#include <stdint.h>

/* Vector/FPU API over N-bit register views. Lane semantics are IEEE binary32/64;
   register widths are arbitrary multiples of lane width. Wider floating-point
   formats require a separately specified software format and are not implied here. */
struct ChimeraNBitFloatView {
    uint8_t *bytes;
    uint32_t width_bits;
    uint32_t capacity_bytes;
};
struct ChimeraNBitConstFloatView {
    const uint8_t *bytes;
    uint32_t width_bits;
    uint32_t capacity_bytes;
};
enum ChimeraNBitFloatOpcode : uint32_t {
    CHIMERA_NBIT_F32_ADD=1, CHIMERA_NBIT_F32_SUB=2,
    CHIMERA_NBIT_F32_MUL=3, CHIMERA_NBIT_F32_DIV=4,
    CHIMERA_NBIT_F64_ADD=5, CHIMERA_NBIT_F64_SUB=6,
    CHIMERA_NBIT_F64_MUL=7, CHIMERA_NBIT_F64_DIV=8
};
class ChimeraNBitFPU final {
public:
    static int execute_lanes(ChimeraNBitFloatView dst, ChimeraNBitConstFloatView lhs,
                             ChimeraNBitConstFloatView rhs, ChimeraNBitFloatOpcode op);
    static uint32_t lane_bits(ChimeraNBitFloatOpcode op);
};
extern "C" int chimera_nbit_fpu_execute(uint8_t *dst,uint32_t dst_capacity,
    const uint8_t *lhs,uint32_t lhs_capacity,const uint8_t *rhs,uint32_t rhs_capacity,
    uint32_t width_bits,uint32_t opcode);
