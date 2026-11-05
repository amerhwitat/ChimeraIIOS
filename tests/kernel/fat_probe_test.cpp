#include "chimera/fat_probe.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
namespace {
uint8_t media[70000u * 512u]{};
void p16(uint8_t *p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
void p32(uint8_t *p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);p[2]=(uint8_t)(v>>16);p[3]=(uint8_t)(v>>24);}
int rd(void*,uint64_t l,uint32_t n,void*b){memcpy(b,media+l*512u,(size_t)n*512u);return 0;}
int wr(void*,uint64_t l,uint32_t n,const void*b){memcpy(media+l*512u,b,(size_t)n*512u);return 0;}
void base(){memset(media,0,sizeof(media));media[510]=0x55;media[511]=0xaa;}
}
int main(){
 const chimera_block_ops ops{rd,wr,nullptr};uint32_t h=0;
 assert(chimera_block_register("fat-test",512,70000,0,&ops,nullptr,&h)==0);
 chimera_fat_probe_info i{};
 base();p16(media+11,512);media[13]=1;p16(media+14,1);media[16]=2;p16(media+17,512);p16(media+19,4000);p16(media+22,12);
 assert(chimera_fat_probe(h,&i)==0 && i.kind==CHM_FAT12 && i.total_sectors==4000);
 base();p16(media+11,512);media[13]=1;p16(media+14,1);media[16]=2;p16(media+17,512);p16(media+19,6000);p16(media+22,24);
 assert(chimera_fat_probe(h,&i)==0 && i.kind==CHM_FAT16);
 base();p16(media+11,512);media[13]=1;p16(media+14,32);media[16]=2;p16(media+17,0);p16(media+19,0);p16(media+22,0);p32(media+32,70000);p32(media+36,600);p32(media+44,2);
 assert(chimera_fat_probe(h,&i)==0 && i.kind==CHM_FAT32 && i.root_cluster==2);
 base();p16(media+11,512);media[13]=1;p16(media+14,1);media[16]=2;p16(media+17,512);p16(media+19,4000);p16(media+22,1);
 assert(chimera_fat_probe(h,&i)==CHM_BLOCK_EINVAL);
 base();memcpy(media+3,"EXFAT   ",8);media[108]=9;media[109]=0;p32(media+72,4096);p32(media+80,24);p32(media+84,32);p32(media+88,56);p32(media+92,100);p32(media+96,2);
 assert(chimera_fat_probe(h,&i)==0 && i.kind==CHM_EXFAT);
 assert(chimera_block_unregister(h)==0);
 return 0;
}
