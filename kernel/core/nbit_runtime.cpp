#include "chimera/nbit_runtime.h"

namespace {
static uint32_t byte_count(uint32_t bits) {
    return (uint32_t)(((uint64_t)bits + 7u) / 8u);
}
static int validate_dst(ChimeraNBitView v) {
    if (!v.bytes || !v.bit_width || v.capacity_bytes < byte_count(v.bit_width)) return -1;
    return 0;
}
static int validate_pair(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    if (validate_dst(d) || ChimeraNBitArithmetic::validate(a) ||
        ChimeraNBitArithmetic::validate(b)) return -1;
    return (d.bit_width == a.bit_width && a.bit_width == b.bit_width) ? 0 : -2;
}
static uint8_t final_mask(uint32_t bits) {
    const uint32_t rem = bits & 7u;
    return rem ? (uint8_t)((1u << rem) - 1u) : 0xffu;
}
}
int ChimeraNBitArithmetic::validate(const ChimeraNBitConstView &v) {
    return (!v.bytes || !v.bit_width || v.capacity_bytes < byte_count(v.bit_width)) ? -1 : 0;
}
void ChimeraNBitArithmetic::mask_top(ChimeraNBitView v) {
    const uint32_t n = byte_count(v.bit_width);
    v.bytes[n - 1u] &= final_mask(v.bit_width);
}
int ChimeraNBitArithmetic::add(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    int rc=validate_pair(d,a,b); if(rc) return rc;
    const uint32_t n=byte_count(d.bit_width); uint32_t carry=0;
    for(uint32_t i=0;i<n;++i) {
        const uint32_t sum=(uint32_t)a.bytes[i]+(uint32_t)b.bytes[i]+carry;
        d.bytes[i]=(uint8_t)sum; carry=sum>>8;
    }
    mask_top(d); return 0;
}
int ChimeraNBitArithmetic::subtract(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    int rc=validate_pair(d,a,b); if(rc) return rc;
    const uint32_t n=byte_count(d.bit_width); uint32_t borrow=0;
    for(uint32_t i=0;i<n;++i) {
        const uint32_t av=a.bytes[i], sub=(uint32_t)b.bytes[i]+borrow;
        d.bytes[i]=(uint8_t)(av-sub); borrow=(av<sub)?1u:0u;
    }
    mask_top(d); return 0;
}
int ChimeraNBitArithmetic::bit_and(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    int rc=validate_pair(d,a,b); if(rc) return rc;
    for(uint32_t i=0,n=byte_count(d.bit_width);i<n;++i)d.bytes[i]=a.bytes[i]&b.bytes[i];
    mask_top(d); return 0;
}
int ChimeraNBitArithmetic::bit_or(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    int rc=validate_pair(d,a,b); if(rc) return rc;
    for(uint32_t i=0,n=byte_count(d.bit_width);i<n;++i)d.bytes[i]=a.bytes[i]|b.bytes[i];
    mask_top(d); return 0;
}
int ChimeraNBitArithmetic::bit_xor(ChimeraNBitView d, ChimeraNBitConstView a, ChimeraNBitConstView b) {
    int rc=validate_pair(d,a,b); if(rc) return rc;
    for(uint32_t i=0,n=byte_count(d.bit_width);i<n;++i)d.bytes[i]=a.bytes[i]^b.bytes[i];
    mask_top(d); return 0;
}
int ChimeraNBitArithmetic::bit_not(ChimeraNBitView d, ChimeraNBitConstView s) {
    if(validate_dst(d)||validate(s))return -1;
    if(d.bit_width!=s.bit_width)return -2;
    for(uint32_t i=0,n=byte_count(d.bit_width);i<n;++i)d.bytes[i]=(uint8_t)~s.bytes[i];
    mask_top(d);return 0;
}
int ChimeraNBitArithmetic::shift_left(ChimeraNBitView d, ChimeraNBitConstView s, uint32_t amount) {
    if(validate_dst(d)||validate(s))return -1;
    if(d.bit_width!=s.bit_width)return -2;
    const uint32_t n=byte_count(d.bit_width);
    if(amount>=d.bit_width){for(uint32_t i=0;i<n;++i)d.bytes[i]=0;return 0;}
    const uint32_t bytes=amount>>3, bits=amount&7u;
    for(uint32_t i=n;i>0;--i) {
        const uint32_t j=i-1u; uint16_t v=0;
        if(j>=bytes){v=(uint16_t)s.bytes[j-bytes]<<bits;
            if(bits&&j>bytes)v|=(uint16_t)s.bytes[j-bytes-1u]>>(8u-bits);}
        d.bytes[j]=(uint8_t)v;
    }
    mask_top(d);return 0;
}
int ChimeraNBitArithmetic::shift_right(ChimeraNBitView d, ChimeraNBitConstView s, uint32_t amount) {
    if(validate_dst(d)||validate(s))return -1;
    if(d.bit_width!=s.bit_width)return -2;
    const uint32_t n=byte_count(d.bit_width);
    if(amount>=d.bit_width){for(uint32_t i=0;i<n;++i)d.bytes[i]=0;return 0;}
    const uint32_t bytes=amount>>3, bits=amount&7u;
    for(uint32_t i=0;i<n;++i) {
        uint16_t v=0;
        if(i+bytes<n){v=(uint16_t)s.bytes[i+bytes]>>bits;
            if(bits&&i+bytes+1u<n)v|=(uint16_t)s.bytes[i+bytes+1u]<<(8u-bits);}
        d.bytes[i]=(uint8_t)v;
    }
    mask_top(d);return 0;
}
int ChimeraNBitArithmetic::compare_unsigned(ChimeraNBitConstView a, ChimeraNBitConstView b) {
    if(validate(a)||validate(b))return 0;
    if(a.bit_width!=b.bit_width)return (a.bit_width<b.bit_width)?-2:2;
    const uint32_t n=byte_count(a.bit_width);
    for(uint32_t i=n;i>0;--i){
        uint8_t av=a.bytes[i-1u],bv=b.bytes[i-1u];
        if(i==n){const uint8_t mask=final_mask(a.bit_width);av&=mask;bv&=mask;}
        if(av<bv)return -1;\n        if(av>bv)return 1;
    }
    return 0;
}
extern "C" int chimera_nbit_word_add(uint8_t*d,uint32_t dc,const uint8_t*a,uint32_t ac,const uint8_t*b,uint32_t bc,uint32_t bits) {
    return ChimeraNBitArithmetic::add({d,bits,dc},{a,bits,ac},{b,bits,bc});
}
extern "C" int chimera_nbit_word_subtract(uint8_t*d,uint32_t dc,const uint8_t*a,uint32_t ac,const uint8_t*b,uint32_t bc,uint32_t bits) {
    return ChimeraNBitArithmetic::subtract({d,bits,dc},{a,bits,ac},{b,bits,bc});
}

extern "C" int chimera_nbit_batch_add(uint8_t *dst,uint32_t dc,const uint8_t *lhs,uint32_t lc,
                                        const uint8_t *rhs,uint32_t rc,uint32_t bits,
                                        uint32_t stride,uint32_t first,uint32_t count) {
    if (!count) return 0;
    if (!dst || !lhs || !rhs || !bits) return -1;
    const uint32_t bytes=byte_count(bits);
    if (stride < bytes) return -2;
    const uint64_t end=(uint64_t)first+(uint64_t)count;
    if (end > (uint64_t)UINT32_MAX+1u) return -3;
    const uint64_t last_offset=(end-1u)*(uint64_t)stride;
    if (last_offset+bytes>dc || last_offset+bytes>lc || last_offset+bytes>rc) return -4;
    for(uint32_t i=0;i<count;++i) {
        const uint64_t offset=((uint64_t)first+i)*(uint64_t)stride;
        int result=ChimeraNBitArithmetic::add(
            {dst+(size_t)offset,bits,dc-(uint32_t)offset},
            {lhs+(size_t)offset,bits,lc-(uint32_t)offset},
            {rhs+(size_t)offset,bits,rc-(uint32_t)offset});
        if(result)return result;
    }
    return 0;
}
