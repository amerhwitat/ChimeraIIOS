#include "chimera/acpi_rsdp.h"
#include <stddef.h>
#include <stdint.h>
namespace {
constexpr uint64_t kMaxTable=1024u*1024u, kBiosStart=0xE0000u, kBiosEnd=0x100000u;
constexpr uint64_t kEbdaPointer=0x40Eu, kV1=20u, kV2=36u, kHeader=36u;
static uint16_t le16(const uint8_t*p){return (uint16_t)p[0]|((uint16_t)p[1]<<8);}
static uint32_t le32(const uint8_t*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint64_t le64(const uint8_t*p){return (uint64_t)le32(p)|((uint64_t)le32(p+4)<<32);}
static bool sig(const uint8_t*p,const char*s,size_t n){for(size_t i=0;i<n;i++)if(p[i]!=(uint8_t)s[i])return false;return true;}
static bool sum_ok(const uint8_t*p,uint64_t n){uint8_t s=0;for(uint64_t i=0;i<n;i++)s=(uint8_t)(s+p[i]);return s==0;}
static bool add_ok(uint64_t a,uint64_t b,uint64_t*out){if(a>UINT64_MAX-b)return false;*out=a+b;return true;}
static bool rsdp_at(koronos_acpi_map_fn map,void*ctx,uint64_t phys){
 const uint8_t *p = map(phys, kV1, ctx);
 if (!p || !sig(p, "RSD PTR ", 8) || !sum_ok(p, kV1)) return false;
 if (p[15] < 2) return true;
 p=map(phys,kV2,ctx);if(!p)return false;uint32_t len=le32(p+20);
 if (len < kV2 || len > 4096u) return false;
 p = map(phys, len, ctx);
 return p && sum_ok(p, len);
}
static bool scan(koronos_acpi_map_fn map,void*ctx,uint64_t start,uint64_t end,uint64_t*out){
 uint64_t a;if(!add_ok(start,15,&a))return false;a&=~15ull;
 for(;a<=end&&end-a>=kV1;a+=16){if(rsdp_at(map,ctx,a)){*out=a;return true;}if(a>UINT64_MAX-16)break;}return false;
}
}
extern "C" int koronos_acpi_find_rsdp(koronos_acpi_map_fn map,void*ctx,uint64_t*out){
 if (!out) return -1;
 *out = 0;
 if (!map) return -2;
 const uint8_t *bda = map(kEbdaPointer, 2, ctx);
 if(bda){uint64_t ebda=(uint64_t)le16(bda)<<4, end;
 if(ebda>=0x400&&ebda<kBiosStart&&add_ok(ebda,1024,&end)&&end<=kBiosStart&&scan(map,ctx,ebda,end,out))return 0;}
 return scan(map,ctx,kBiosStart,kBiosEnd,out)?0:-3;
}
extern "C" int koronos_acpi_locate_madt(koronos_acpi_map_fn map,void*ctx,uint64_t rsdp_phys,uint64_t*out){
 if (!out) return -1;
 *out = 0;
 if (!map || !rsdp_phys) return -2;
 if (!rsdp_at(map, ctx, rsdp_phys)) return -3;
 const uint8_t*r=map(rsdp_phys,kV1,ctx);if(!r)return -4;uint64_t root=le32(r+16);bool xsdt=false;
 if(r[15]>=2){const uint8_t*r2=map(rsdp_phys,kV2,ctx);if(!r2)return -5;uint64_t x=le64(r2+24);if(x){root=x;xsdt=true;}}
 if (!root) return -6;
 const uint8_t *h = map(root, kHeader, ctx);
 if (!h || !sig(h, xsdt ? "XSDT" : "RSDT", 4)) return -7;
 uint32_t len=le32(h+4),width=xsdt?8u:4u;if(len<kHeader||len>kMaxTable||((len-kHeader)%width))return -8;
 h=map(root,len,ctx);if(!h||!sum_ok(h,len))return -9;uint32_t count=(len-(uint32_t)kHeader)/width;
 for(uint32_t i=0;i<count;i++){uint64_t entry=xsdt?le64(h+kHeader+(uint64_t)i*width):le32(h+kHeader+(uint64_t)i*width);
 if(!entry)continue;const uint8_t*eh=map(entry,kHeader,ctx);if(!eh||!sig(eh,"APIC",4))continue;
 uint32_t ml=le32(eh+4);if(ml<44||ml>kMaxTable)continue;const uint8_t*m=map(entry,ml,ctx);
 if(m&&sum_ok(m,ml)){*out=entry;return 0;}}
 return -10;
}
