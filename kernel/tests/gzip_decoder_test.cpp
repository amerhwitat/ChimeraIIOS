#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "chimera/gzip.h"
using Bytes=std::vector<uint8_t>;
static uint32_t crc32(const uint8_t *p,size_t n) {
    uint32_t c=0xffffffffu; for(size_t j=0;j<n;++j) { c^=p[j]; for(int i=0;i<8;++i)c=(c>>1)^((c&1)?0xedb88320u:0u); } return c^0xffffffffu;
}
static void le32(Bytes &b,uint32_t x){for(int i=0;i<4;++i)b.push_back((uint8_t)(x>>(8*i)));}
static Bytes stored_gzip(const char *s) {
    const size_t n=std::strlen(s); assert(n<65536);
    Bytes b={0x1f,0x8b,8,0,0,0,0,0,0,255,1,(uint8_t)n,(uint8_t)(n>>8),(uint8_t)~n,(uint8_t)(~n>>8)};
    b.insert(b.end(),s,s+n); le32(b,crc32(reinterpret_cast<const uint8_t*>(s),n)); le32(b,(uint32_t)n); return b;
}
static Bytes from_hex(const char *hex) {
    Bytes b;
    while (*hex) {
        while (*hex==' ' || *hex=='\n' || *hex=='\t') ++hex;
        if (!*hex) break;
        auto digit=[](char c)->uint8_t { return c>='0'&&c<='9' ? c-'0' : c>='a'&&c<='f' ? c-'a'+10 : c-'A'+10; };
        uint8_t hi=digit(*hex++); assert(*hex);
        uint8_t lo=digit(*hex++); b.push_back(static_cast<uint8_t>((hi<<4)|lo));
    }
    return b;
}
static bool reject(Bytes b,uint64_t cap=4096) {
    uint8_t out[4096]; uint64_t n=99;
    return chimera_gzip_decompress_bounded(b.data(),b.size(),out,cap,&n)!=0 && n==0;
}
static void check_fixture(const char *hex, const char *label) {
    const char *prefix="Koronos gzip integration regression: ";
    const char *repeat="bounded native initramfs payload ";
    Bytes expected(prefix, prefix+std::strlen(prefix));
    for(int i=0;i<20;++i) expected.insert(expected.end(),repeat,repeat+std::strlen(repeat));
    Bytes gz=from_hex(hex); uint8_t out[4096]={0}; uint64_t n=0;
    const int rc=chimera_gzip_decompress_bounded(gz.data(),gz.size(),out,sizeof(out),&n);
    if(rc!=0 || n!=expected.size() || std::memcmp(out,expected.data(),expected.size())!=0) {
        std::fprintf(stderr,"%s Huffman fixture failed: rc=%d size=%llu expected=%llu\n",label,rc,(unsigned long long)n,(unsigned long long)expected.size());
        std::abort();
    }
}
int main() {
    Bytes gz=stored_gzip("bounded gzip works");
    uint8_t out[4096]={0}; uint64_t n=0;
    assert(chimera_gzip_decompress_bounded(gz.data(),gz.size(),out,sizeof(out),&n)==0);
    assert(n==18 && std::memcmp(out,"bounded gzip works",18)==0);
    assert(reject(gz,4));
    Bytes bad=gz; bad[bad.size()-8]^=1; assert(reject(bad));
    bad=gz; bad[3]=0xe0; assert(reject(bad));
    bad=gz; bad[3]=0x02; assert(reject(bad)); // FHCRC is deliberately unsupported.
    bad=gz; bad.insert(bad.end()-8,0x7f); assert(reject(bad)); // Extra bytes before trailer.
    bad=gz; bad.pop_back(); assert(reject(bad));
    bad={0x1f,0x8b,8,0,0,0,0,0,0,255,7}; assert(reject(bad));
    /* Independent zlib-generated streams: first DEFLATE block is fixed (BTYPE=1),
       second is dynamic (BTYPE=2); both expand to the same 697-byte payload. */
    check_fixture("1f8b08000000000002fff3ce2fcacfcb2f5648afca2c50c8cc2b494d2f4a2cc9cccf532802b2528b8b814c2b85a4fcd2bc94d414853ca054592a5059664951626e5ab1424162654e7e62caa8825105f45600003de2e12ab9020000","fixed");
    check_fixture("1f8b08000000000002ffedcac10980400c05d15652872d584564e312d0fc258982566faaf0b4b781792b1c86a0feea20b594ee9c0a23af9288ca85365cd6a491d5baa598a6f3b9070d7e0e709b6082bfc1073de2e12ab9020000","dynamic");
    std::puts("bounded gzip/DEFLATE tests: PASS");
}
