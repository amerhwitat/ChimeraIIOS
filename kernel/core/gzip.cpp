#include <stdint.h>
#include <stddef.h>
#include "chimera/gzip.h"

namespace {
struct Bits {
    const uint8_t *p; uint64_t n, pos; uint32_t hold, have;
    bool get(uint32_t count, uint32_t *v) {
        if (count > 24u || !v) return false;
        while (have < count) {
            if (pos >= n) return false;
            hold |= static_cast<uint32_t>(p[pos++]) << have;
            have += 8u;
        }
        *v = hold & ((count == 32u) ? 0xffffffffu : ((1u << count) - 1u));
        hold >>= count; have -= count; return true;
    }
    bool align() { hold = 0; have = 0; return true; }
};
struct Huff {
    uint16_t code[288]; uint8_t length[288]; uint16_t count; uint8_t maxlen;
};
static uint32_t reverse_bits(uint32_t x, uint32_t n) {
    uint32_t r=0; while(n--) { r=(r<<1)|(x&1u); x>>=1; } return r;
}
static bool build(Huff *h, const uint8_t *lens, uint32_t n) {
    uint16_t counts[16]={0}, next[16]={0};
    if (!h || !lens || n>288u) return false;
    h->count=static_cast<uint16_t>(n); h->maxlen=0;
    for(uint32_t i=0;i<n;++i) {
        if(lens[i]>15u) return false;
        if(lens[i]) { ++counts[lens[i]]; if(lens[i]>h->maxlen) h->maxlen=lens[i]; }
    }
    int32_t left=1;
    for(uint32_t bits=1;bits<=15;++bits) { left=(left<<1)-counts[bits]; if(left<0) return false; }
    if(h->maxlen==0) return false;
    uint32_t code=0;
    for(uint32_t bits=1;bits<=15;++bits) { code=(code+counts[bits-1u])<<1; next[bits]=static_cast<uint16_t>(code); }
    for(uint32_t i=0;i<n;++i) {
        h->length[i]=lens[i]; h->code[i]=lens[i] ? static_cast<uint16_t>(reverse_bits(next[lens[i]]++,lens[i])) : 0;
    }
    return true;
}
static int symbol(Bits *b, const Huff *h) {
    uint32_t code=0;
    for(uint32_t len=1;len<=h->maxlen;++len) {
        uint32_t bit=0; if(!b->get(1,&bit)) return -1;
        code |= bit << (len-1u);
        for(uint32_t s=0;s<h->count;++s)
            if(h->length[s]==len && h->code[s]==code) return static_cast<int>(s);
    }
    return -1;
}
static uint32_t crc32_byte(uint32_t crc,uint8_t b) {
    crc^=b; for(uint32_t i=0;i<8;++i) crc=(crc>>1)^((crc&1u)?0xedb88320u:0u); return crc;
}
static uint32_t le32(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1])<<8) |
           (static_cast<uint32_t>(p[2])<<16) | (static_cast<uint32_t>(p[3])<<24);
}
static const uint16_t len_base[29]={3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258};
static const uint8_t len_extra[29]={0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0};
static const uint16_t dist_base[30]={1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577};
static const uint8_t dist_extra[30]={0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13};
static bool fixed(Huff *lit,Huff *dist) {
    uint8_t ll[288],dd[32];
    for(uint32_t i=0;i<=143;++i) ll[i]=8;
    for(uint32_t i=144;i<=255;++i) ll[i]=9;
    for(uint32_t i=256;i<=279;++i) ll[i]=7;
    for(uint32_t i=280;i<288;++i) ll[i]=8;
    for(uint32_t i=0;i<32;++i) dd[i]=5;
    return build(lit,ll,288)&&build(dist,dd,32);
}
static bool dynamic(Bits *b,Huff *lit,Huff *dist) {
    uint32_t a=0,c=0,d=0;
    if(!b->get(5,&a)||!b->get(5,&c)||!b->get(4,&d)) return false;
    uint32_t nl=a+257u, nd=c+1u, nc=d+4u;
    if(nl>286u||nd>32u) return false;
    static const uint8_t order[19]={16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15};
    uint8_t cl[19]={0}, lengths[318]={0};
    for(uint32_t i=0;i<nc;++i) { uint32_t v=0; if(!b->get(3,&v)) return false; cl[order[i]]=static_cast<uint8_t>(v); }
    Huff ch{}; if(!build(&ch,cl,19)) return false;
    uint32_t used=0, total=nl+nd;
    while(used<total) {
        int s=symbol(b,&ch); if(s<0) return false;
        if(s<=15) lengths[used++]=static_cast<uint8_t>(s);
        else {
            uint32_t extra=0,rep=0; uint8_t value=0;
            if(s==16) { if(used==0||!b->get(2,&extra)) return false; rep=extra+3u; value=lengths[used-1u]; }
            else if(s==17) { if(!b->get(3,&extra)) return false; rep=extra+3u; }
            else if(s==18) { if(!b->get(7,&extra)) return false; rep=extra+11u; }
            else return false;
            if(rep>total-used) return false;
            while(rep--) lengths[used++]=value;
        }
    }
    if(lengths[256]==0) return false;
    for(uint32_t i=nl;i<total;++i) if(lengths[i]>0 && i-nl>=30u) return false;
    return build(lit,lengths,nl)&&build(dist,lengths+nl,nd);
}
static int inflate(Bits *b,uint8_t *out,uint64_t cap,uint64_t *used) {
    uint64_t op=0; bool last=false;
    while(!last) {
        uint32_t l=0,t=0;
        if(!b->get(1,&l)||!b->get(2,&t)) return -1;
        last=l!=0;
        if(t==0) {
            b->align(); uint32_t n=0,inv=0;
            if(!b->get(16,&n)||!b->get(16,&inv)) return -1;
            if((n^0xffffu)!=inv) return -2;
            if(n>cap-op) return -3;
            for(uint32_t i=0;i<n;++i) { uint32_t v=0; if(!b->get(8,&v)) return -1; out[op++]=static_cast<uint8_t>(v); }
            continue;
        }
        if(t==3) return -2;
        Huff lit{},dist{};
        if(t==1) { if(!fixed(&lit,&dist)) return -2; }
        else if(!dynamic(b,&lit,&dist)) return -2;
        for(;;) {
            int s=symbol(b,&lit); if(s<0) return -1;
            if(s<256) { if(op>=cap) return -3; out[op++]=static_cast<uint8_t>(s); continue; }
            if(s==256) break;
            if(s<257||s>285) return -2;
            uint32_t li=static_cast<uint32_t>(s-257), ex=0;
            if(len_extra[li] && !b->get(len_extra[li],&ex)) return -1;
            uint32_t length=len_base[li]+ex;
            int d=symbol(b,&dist); if(d<0||d>=30) return -2;
            ex=0; if(dist_extra[d]&&!b->get(dist_extra[d],&ex)) return -1;
            uint32_t distance=dist_base[d]+ex;
            if(distance==0||distance>op) return -2;
            if(length>cap-op) return -3;
            for(uint32_t i=0;i<length;++i) { out[op]=out[op-distance]; ++op; }
        }
    }
    *used=op; return 0;
}
}
extern "C" int chimera_gzip_decompress_bounded(const void *input,uint64_t input_size,
                                                void *output,uint64_t capacity,uint64_t *output_size) {
    if(output_size) *output_size=0;
    if(!input||!output||!output_size||input_size<18u) return -1;
    const uint8_t *in=static_cast<const uint8_t *>(input);
    if(in[0]!=0x1f||in[1]!=0x8b||in[2]!=8u) return -2;
    const uint8_t flags=in[3]; if(flags&0xe2u) return -2; /* Reserved bits and FHCRC are not accepted until header CRC16 is implemented. */
    uint64_t pos=10;
    if(flags&4u) { if(pos+2u>input_size-8u) return -1; uint32_t n=in[pos]|(static_cast<uint32_t>(in[pos+1])<<8); pos+=2; if(n>input_size-8u-pos) return -1; pos+=n; }
    for(uint8_t bit=8u;bit<=16u;bit<<=1) if(flags&bit) {
        while(pos<input_size-8u && in[pos++]!=0) {}
        if(pos>input_size-8u || in[pos-1u]!=0) return -1;
    }
    if(pos>=input_size-8u) return -1;
    Bits b{in+pos,input_size-pos-8u,0,0,0};
    uint64_t produced=0; int rc=inflate(&b,static_cast<uint8_t *>(output),capacity,&produced);
    if(rc) return rc;
    /* Accept exactly one complete member: reject trailing/concatenated DEFLATE bytes. */
    if(b.pos!=b.n) return -5;
    const uint64_t trailer=input_size-8u;
    {
        uint32_t crc=0xffffffffu;
        const uint8_t *out=static_cast<const uint8_t *>(output);
        for(uint64_t i=0;i<produced;++i) crc=crc32_byte(crc,out[i]);
        crc^=0xffffffffu;
        if(crc!=le32(in+trailer)) return -4;
    }
    if(static_cast<uint32_t>(produced)!=le32(in+trailer+4u)) return -4;
    *output_size=produced; return 0;
}
