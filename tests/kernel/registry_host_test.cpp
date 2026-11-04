#include "chimera/registry.h"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>
static void p16(uint8_t*p,uint16_t v){p[0]=v&255;p[1]=v>>8;}
static void p32(uint8_t*p,uint32_t v){for(int i=0;i<4;++i)p[i]=(v>>(8*i))&255;}
static void p64(uint8_t*p,uint64_t v){for(int i=0;i<8;++i)p[i]=(v>>(8*i))&255;}
int main(){uint8_t h[85]={};std::memcpy(h,"CHMRG01",7);p16(h+8,1);p32(h+12,40);p32(h+16,sizeof(h));p32(h+20,2);p64(h+24,9);
 uint32_t o=40;p16(h+o,12);h[o+2]=3;p32(h+o+4,1);o+=8;std::memcpy(h+o,"kernel.debug",12);o+=12;h[o++]=1;
 p16(h+o,12);h[o+2]=1;p32(h+o+4,4);o+=8;std::memcpy(h+o,"cpu.loglevel",12);o+=12;p32(h+o,4);o+=4;assert(o==sizeof(h));
 p32(h+32,koronos_registry_crc32(h+40,sizeof(h)-40));p32(h+36,koronos_registry_crc32(h,36));koronos_registry_view v{};
 assert(koronos_registry_validate(h,sizeof(h),&v));uint8_t b=0;uint64_t n=0;assert(v.generation==9&&v.entry_count==2);
 assert(koronos_registry_read_bool(&v,"kernel.debug",&b)&&b==1);assert(koronos_registry_read_u64(&v,"cpu.loglevel",&n)&&n==4);assert(!koronos_registry_read_u64(&v,"kernel.debug",&n));
 h[sizeof(h)-1]^=1;assert(!koronos_registry_validate(h,sizeof(h),&v));std::puts("[registry-host] PASS");
}
