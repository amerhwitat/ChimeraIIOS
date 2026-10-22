#include "../include/chimera/process_loader.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
struct Region{uint64_t base=0,size=0;uint32_t flags=0;uint8_t bytes[65536]{};};
struct Mock{Region regions[8]{};uint32_t count=0;bool destroyed=false;};
static void*create_as(void*p){auto*m=(Mock*)p;m->count=0;m->destroyed=false;return m;}
static int map_pages(void*p,void*as,uint64_t base,uint64_t size,uint32_t flags,void**alias){
 auto*m=(Mock*)p;if(as!=p||!alias||size>sizeof(m->regions[0].bytes)||m->count>=8)return -1;
 for(uint32_t i=0;i<m->count;i++)if(base<m->regions[i].base+m->regions[i].size&&m->regions[i].base<base+size)return -2;
 auto&r=m->regions[m->count++];r.base=base;r.size=size;r.flags=flags;*alias=r.bytes;return 0;
}
static void destroy_as(void*p,void*as){assert(p==as);((Mock*)p)->destroyed=true;}
static void put16(uint8_t*p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void put32(uint8_t*p,uint32_t v){for(int i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static void put64(uint8_t*p,uint64_t v){for(int i=0;i<8;i++)p[i]=(uint8_t)(v>>(8*i));}
static void build_elf(uint8_t*b,size_t n){
 for(size_t i=0;i<n;i++) b[i]=0;
 b[0]=0x7f; b[1]='E'; b[2]='L'; b[3]='F'; b[4]=2; b[5]=1; b[6]=1;
 put16(b+16,KORONOS_ET_EXEC);put16(b+18,KORONOS_EM_X86_64);put32(b+20,1);put64(b+24,0x400100);put64(b+32,64);
 put16(b+52,64);put16(b+54,56);put16(b+56,1);put32(b+64,1);put32(b+68,5);put64(b+72,0x100);
 put64(b+80,0x400100);put64(b+96,4);put64(b+104,8192);put64(b+112,4096);
 b[0x100]=0x90;b[0x101]=0x90;b[0x102]=0x90;b[0x103]=0xc3;
}
int main(){
 uint8_t elf[512];build_elf(elf,sizeof(elf));chimera_elf_load_ops ops{create_as,map_pages,destroy_as};Mock m{};chimera_loaded_elf loaded{};
 int rc=chimera_elf_load_user_image(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,8192,&ops,&m,&loaded);
 assert(rc==0&&loaded.entry==0x400100&&loaded.segment_count==1&&loaded.loaded_file_bytes==4);
 assert(m.count==2&&!m.destroyed&&m.regions[0].base==0x400000&&m.regions[0].flags==5);
 assert(m.regions[0].bytes[0x100]==0x90&&m.regions[0].bytes[0x103]==0xc3);
 for(size_t i=0x104;i<0x2100;i++)assert(m.regions[0].bytes[i]==0);
 assert(m.regions[1].base==0x6fe000&&m.regions[1].flags==6);
 // Header version and exact ELF header size are mandatory.
 build_elf(elf,sizeof(elf)); put32(elf+20,2); Mock bad_version{}; chimera_loaded_elf untouched{};
 assert(chimera_elf_load_user_image(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,8192,&ops,&bad_version,&untouched)<0);
 assert(bad_version.count==0);
 build_elf(elf,sizeof(elf)); put16(elf+52,63); Mock bad_header{};
 assert(chimera_elf_load_user_image(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,8192,&ops,&bad_header,&untouched)<0);
 assert(bad_header.count==0);
 // Reject mappings in the first user page (null/low-memory guard).
 build_elf(elf,sizeof(elf)); put64(elf+24,0x200); put64(elf+80,0x100); Mock low_page{};
 assert(chimera_elf_load_user_image(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,8192,&ops,&low_page,&untouched)<0);
 assert(low_page.count==0);
 build_elf(elf,sizeof(elf)); put32(elf+68,7); Mock bad_wx{};
 assert(chimera_elf_load_user_image(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,8192,&ops,&bad_wx,&untouched)<0);
 assert(bad_wx.count==0);
 puts("process loader: PT_LOAD copy, BSS zeroing, header/version, low-page guard, W^X and stack mapping passed");return 0;
}
