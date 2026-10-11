#include "chimera/nbit_runtime.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main() {
    uint8_t a[2]={0xf0,0x1f}, b[2]={0x30,0x00}, out[2]={};
    ChimeraNBitConstView av{a,13,2}, bv{b,13,2};
    ChimeraNBitView ov{out,13,2};
    assert(ChimeraNBitArithmetic::validate(av)==0);
    assert(ChimeraNBitArithmetic::add(ov,av,bv)==0);
    assert(out[0]==0x20 && out[1]==0x00); // 13-bit wraparound
    assert(ChimeraNBitArithmetic::subtract(ov,{out,13,2},bv)==0);
    assert(out[0]==0xf0 && out[1]==0x1f);
    assert(ChimeraNBitArithmetic::bit_and(ov,av,bv)==0);
    assert(out[0]==0x30 && out[1]==0x00);
    assert(ChimeraNBitArithmetic::bit_or(ov,av,bv)==0);
    assert(out[0]==0xf0 && out[1]==0x1f);
    assert(ChimeraNBitArithmetic::shift_left(ov,bv,4)==0);
    assert(out[0]==0x00 && out[1]==0x03);
    assert(ChimeraNBitArithmetic::shift_right(ov,{out,13,2},4)==0);
    assert(out[0]==0x30 && out[1]==0x00);
    assert(ChimeraNBitArithmetic::compare_unsigned(av,bv)==1);

    /* Arbitrary width beyond the former 8192-bit ceiling, no heap allocation. */
    uint8_t wide_a[1025]={}, wide_b[1025]={}, wide_out[1025]={};
    wide_a[1024]=1; wide_b[0]=2;
    ChimeraNBitConstView wa{wide_a,8193,1025}, wb{wide_b,8193,1025};
    ChimeraNBitView wo{wide_out,8193,1025};
    assert(ChimeraNBitArithmetic::add(wo,wa,wb)==0);
    assert(wide_out[1024]==1 && wide_out[0]==2);
    assert(ChimeraNBitArithmetic::shift_left(wo,wb,8192)==0);
    assert(wide_out[1024]==0 && wide_out[0]==0); // bit 8193 shifted out
    assert(ChimeraNBitArithmetic::add({wide_out,8193,1},wa,wb)==-1);
    assert(ChimeraNBitArithmetic::add({wide_out,8192,1025},wa,wb)==-2);
    puts("Arbitrary-width N-bit arithmetic passed.");
    return 0;
}
