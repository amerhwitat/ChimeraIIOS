#include "chimera/acpi_rsdp.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
static uint8_t mem[0x110000];
static const uint8_t* mapmem(uint64_t p,uint64_t n,void*){if(p>sizeof(mem)||n>sizeof(mem)-p)return nullptr;return mem+p;}
static void sum(uint8_t*p,uint32_t n,uint32_t off){p[off]=0;uint8_t s=0;for(uint32_t i=0;i<n;i++)s=(uint8_t)(s+p[i]);p[off]=(uint8_t)(0-s);}
static void header(uint8_t*p,const char*s,uint32_t n){memset(p,0,n);memcpy(p,s,4);p[4]=n;p[5]=n>>8;p[6]=n>>16;p[7]=n>>24;}
static void setup(bool xsdt){
 memset(mem,0,sizeof(mem));mem[0x40e]=0;mem[0x40f]=0x80;
 uint8_t*r=mem+0x80000;memcpy(r,"RSD PTR ",8);r[15]=xsdt?2:0;
 if(xsdt){r[20]=36;r[24]=0x00;r[25]=0x10;r[26]=0x08;sum(r,36,32);sum(r,20,8);}
 else{r[16]=0;r[17]=0x10;r[18]=0x08;sum(r,20,8);}
 uint8_t*root=mem+0x81000;header(root,xsdt?"XSDT":"RSDT",xsdt?44:40);
 if(xsdt){root[36]=0;root[37]=0x20;root[38]=0x08;sum(root,44,9);}
 else{root[36]=0;root[37]=0x20;root[38]=0x08;sum(root,40,9);}
 uint8_t*m=mem+0x82000;header(m,"APIC",44);sum(m,44,9);
}
int main(){
 uint64_t found=0,madt=0;setup(false);
 assert(koronos_acpi_find_rsdp(mapmem,nullptr,&found)==0&&found==0x80000);
 assert(koronos_acpi_locate_madt(mapmem,nullptr,found,&madt)==0&&madt==0x82000);
 mem[0x81000+9]^=1;assert(koronos_acpi_locate_madt(mapmem,nullptr,found,&madt)==-9&&madt==0);
 setup(true);found=0;madt=0;
 assert(koronos_acpi_find_rsdp(mapmem,nullptr,&found)==0&&found==0x80000);
 assert(koronos_acpi_locate_madt(mapmem,nullptr,found,&madt)==0&&madt==0x82000);
 mem[0x80000+32]^=1;assert(koronos_acpi_locate_madt(mapmem,nullptr,found,&madt)==-3&&madt==0);
 memset(mem+0x80000,0,1024);assert(koronos_acpi_find_rsdp(mapmem,nullptr,&found)==-3);
 assert(koronos_acpi_find_rsdp(mapmem,nullptr,nullptr)==-1);return 0;
}