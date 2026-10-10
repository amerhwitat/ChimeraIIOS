#include "chimera/physmem.h"
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>
#pragma pack(push,1)
struct Tag { uint32_t type,size; };
struct MmapHead { uint32_t entry_size,entry_version; };
struct MmapEntry { uint64_t address,length; uint32_t type,reserved; };
#pragma pack(pop)
static void append(std::vector<uint8_t>&v,const void*p,size_t n){const auto*b=(const uint8_t*)p;v.insert(v.end(),b,b+n);}
static void tag(std::vector<uint8_t>&v,uint32_t type,const void*body,uint32_t bodySize){Tag t{type,(uint32_t)sizeof(Tag)+bodySize};append(v,&t,sizeof(t));if(bodySize)append(v,body,bodySize);while(v.size()%8)v.push_back(0);}
int main(){
 std::vector<uint8_t> info(8,0);
 MmapHead mh{sizeof(MmapEntry),0};
 std::vector<uint8_t> body;append(body,&mh,sizeof(mh));
 MmapEntry a{0,0x100000,1,0}, b{0x100000,0x3f00000,1,0}, reserved{0x800000,0x100000,2,0};
 append(body,&a,sizeof(a));append(body,&b,sizeof(b));append(body,&reserved,sizeof(reserved));
 tag(info,6,body.data(),(uint32_t)body.size());
 uint8_t moduleBody[8]={0};uint32_t modStart=0x500000,modEnd=0x510000;std::memcpy(moduleBody,&modStart,4);std::memcpy(moduleBody+4,&modEnd,4);tag(info,3,moduleBody,sizeof(moduleBody));
 tag(info,0,nullptr,0);
 uint32_t total=(uint32_t)info.size();std::memcpy(info.data(),&total,4);
 const uint64_t kernelStart=0x200000,kernelEnd=0x280000;
 assert(chimera_physmem_init((uint64_t)(uintptr_t)info.data(),kernelStart,kernelEnd)==0);
 assert(chimera_physmem_ready()==1);
 const uint64_t before=chimera_physmem_free_pages();assert(before>0);
 std::vector<uint64_t> pages;
 for(int i=0;i<32;i++){uint64_t p=0;assert(chimera_physmem_alloc_page(&p)==0);assert(p>=0x100000&&p<0x4000000);assert((p&4095)==0);assert(!(p>=kernelStart&&p<kernelEnd));assert(!(p>=modStart&&p<modEnd));assert(!(p>=0x800000&&p<0x900000));pages.push_back(p);}
 assert(chimera_physmem_free_pages()==before-32);
 assert(chimera_physmem_free_page(pages[0])==0);assert(chimera_physmem_free_page(pages[0])==-2);
 assert(chimera_physmem_free_page(pages[1]+1)==-1);assert(chimera_physmem_free_pages()==before-31);
 for(size_t i=1;i<pages.size();i++)assert(chimera_physmem_free_page(pages[i])==0);
 assert(chimera_physmem_free_pages()==before);
 assert(chimera_physmem_init(0,kernelStart,kernelEnd)<0);
 assert(chimera_physmem_ready()==0);
}
