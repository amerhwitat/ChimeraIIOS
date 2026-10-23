#include "chimera/block_device.h"
#include "chimera/iso9660.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
static uint8_t disk[20u*2048u];
static int rd(void*,uint64_t o,void*b,uint64_t n){memcpy(b,disk+o,(size_t)n);return 0;}
static int wr(void*,uint64_t o,const void*b,uint64_t n){memcpy(disk+o,b,(size_t)n);return 0;}
static void both32(uint8_t*p,uint32_t v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;p[4]=v>>24;p[5]=v>>16;p[6]=v>>8;p[7]=v;}
static void both16(uint8_t*p,uint16_t v){p[0]=v;p[1]=v>>8;p[2]=v>>8;p[3]=v;}
static uint32_t record(uint8_t*p,uint32_t extent,uint32_t size,uint8_t flags,const uint8_t*name,uint8_t nl){uint8_t n=(uint8_t)(33+nl+((nl%2)==0));memset(p,0,n);p[0]=n;both32(p+2,extent);both32(p+10,size);p[25]=flags;p[32]=nl;memcpy(p+33,name,nl);return n;}
int main(){
 chimera_block_device d{CHIMERA_BLOCK_DEVICE_ABI,512,sizeof(disk),0,nullptr,rd,wr,nullptr,nullptr};
 assert(chimera_block_read(&d,sizeof(disk),disk,1)==-5);
 assert(chimera_block_write(&d,sizeof(disk),disk,1)==-5);
 d.flags=CHIMERA_BLOCK_READ_ONLY;assert(chimera_block_write(&d,0,disk,1)==-30);d.flags=0;
 uint8_t*p=disk+16*2048;p[0]=1;memcpy(p+1,"CD001",5);p[6]=1;both32(p+80,20);both16(p+128,2048);uint8_t rootname=0;record(p+156,18,2048,2,&rootname,1);
 uint8_t*term=disk+17*2048;term[0]=255;memcpy(term+1,"CD001",5);term[6]=1;
 uint8_t*dir=disk+18*2048;uint8_t dot=0,dotdot=1;uint32_t pos=record(dir,18,2048,2,&dot,1);pos+=record(dir+pos,18,2048,2,&dotdot,1);uint8_t fname[]="HELLO.TXT;1";pos+=record(dir+pos,19,5,0,fname,sizeof(fname)-1);
 memcpy(disk+19*2048,"hello",5);
 chimera_iso9660*fs=nullptr;assert(chimera_iso9660_mount(&d,&fs)==0&&fs);
 auto ops=chimera_iso9660_vfs_ops();chimera_vfs_stat st{};assert(ops->lookup(fs,"/HELLO.TXT",&st)==0&&st.size==5);
 char out[6]={};uint64_t got=0;assert(ops->read(fs,"/HELLO.TXT",0,out,5,&got)==0&&got==5&&memcmp(out,"hello",5)==0);
 assert(ops->write==nullptr&&ops->create==nullptr);
 assert(ops->lookup(fs,"/../HELLO.TXT",&st)!=0);
 chimera_iso9660_unmount(fs);puts("block_device_iso9660_test: PASS");return 0;
}
