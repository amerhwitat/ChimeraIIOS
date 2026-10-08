#ifndef CHIMERA_NBIT_RUNTIME_H
#define CHIMERA_NBIT_RUNTIME_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Stable v1 ABI: little-endian arrays of uint64_t limbs; capacity is in limbs.
 * Functions return 0 on success, -1 on invalid input, -2 on divide-by-zero. */
#define CHIMERA_NBIT_ABI_VERSION 1u
int chimera_nbit_add_u64(uint64_t *out,const uint64_t *a,const uint64_t *b,size_t n,uint64_t *carry);
int chimera_nbit_sub_u64(uint64_t *out,const uint64_t *a,const uint64_t *b,size_t n,uint64_t *borrow);
int chimera_nbit_mul_u64(uint64_t *out,size_t out_n,const uint64_t *a,size_t a_n,const uint64_t *b,size_t b_n);
int chimera_nbit_and_u64(uint64_t *out,const uint64_t *a,const uint64_t *b,size_t n);
int chimera_nbit_or_u64(uint64_t *out,const uint64_t *a,const uint64_t *b,size_t n);
int chimera_nbit_xor_u64(uint64_t *out,const uint64_t *a,const uint64_t *b,size_t n);
int chimera_nbit_not_u64(uint64_t *out,const uint64_t *a,size_t n);
int chimera_nbit_shl_u64(uint64_t *out,const uint64_t *a,size_t n,size_t shift_bits);
int chimera_nbit_shr_u64(uint64_t *out,const uint64_t *a,size_t n,size_t shift_bits);
int chimera_nbit_cmp_u64(const uint64_t *a,const uint64_t *b,size_t n); /* -1,0,1 */
int chimera_nbit_divmod_u64(uint64_t *q,uint64_t *r,const uint64_t *a,size_t n,const uint64_t *b,size_t m);
uint32_t chimera_nbit_f32_add(uint32_t a_bits,uint32_t b_bits);
uint32_t chimera_nbit_f32_mul(uint32_t a_bits,uint32_t b_bits);
uint32_t chimera_nbit_f32_div(uint32_t a_bits,uint32_t b_bits);
uint64_t chimera_nbit_f64_add(uint64_t a_bits,uint64_t b_bits);
uint64_t chimera_nbit_f64_mul(uint64_t a_bits,uint64_t b_bits);
uint64_t chimera_nbit_f64_div(uint64_t a_bits,uint64_t b_bits);
#ifdef __cplusplus
}
#endif
#endif
