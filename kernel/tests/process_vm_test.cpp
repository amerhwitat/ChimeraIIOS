#include "chimera/process_vm.h"
#include <cassert>
#include <cstdint>
#include <cstring>
alignas(4096) static uint8_t mem[2048][4096];
static bool used[2048];
static int alloc(void*,uint32_t n,uint64_t*p,void**alias){for(uint32_t i=1;i+n<=2048;++i){bool ok=true;for(uint32_t j=0;j<n;++j)if(used[i+j]){ok=false;break;}if(!ok)continue;for(uint32_t j=0;j<n;++j)used[i+j]=true;*p=(uint64_t)i*4096;*alias=mem[i];return 0;}return -1;}
static void release(void*,uint64_t p,uint32_t n){uint32_t i=(uint32_t)(p/4096);for(uint32_t j=0;j<n;++j){assert(i+j<2048);used[i+j]=false;}}
static void*phys(void*,uint64_t p){uint64_t i=p/4096;if(i>=2048||!used[i])return nullptr;return mem[i];}
static uint64_t*walk(uint64_t*pml4,uint64_t va){uint64_t e=pml4[(va>>39)&511];if(!(e&1))return nullptr;auto*l3=(uint64_t*)phys(nullptr,e&0x000FFFFFFFFFF000ull);e=l3[(va>>30)&511];if(!(e&1))return nullptr;auto*l2=(uint64_t*)phys(nullptr,e&0x000FFFFFFFFFF000ull);e=l2[(va>>21)&511];if(!(e&1))return nullptr;auto*l1=(uint64_t*)phys(nullptr,e&0x000FFFFFFFFFF000ull);return &l1[(va>>12)&511];}
int main(){uint64_t boot=0;void*ba=nullptr;assert(alloc(nullptr,1,&boot,&ba)==0);((uint64_t*)ba)[300]=0x12345003;chimera_x86_vm_ops ops{alloc,release,phys,boot,1};assert(chimera_x86_vm_init(&ops,nullptr)==0);auto*s=chimera_x86_vm_create();assert(s);uint64_t pml4p=chimera_x86_vm_pml4_physical(s);auto*pml4=(uint64_t*)phys(nullptr,pml4p);assert(pml4[300]==0x12345003);void*alias=nullptr;assert(chimera_x86_vm_map(s,0x400000,8192,4,&alias)==0);assert(alias);((uint8_t*)alias)[0]=0xC3;uint64_t*pte=walk(pml4,0x400000);assert(pte&&(*pte&CHIMERA_X86_PTE_USER)&&(*pte&CHIMERA_X86_PTE_NX)&&!(*pte&CHIMERA_X86_PTE_WRITABLE));assert(chimera_x86_vm_map(s,0x400000,4096,4,&alias)<0);assert(chimera_x86_vm_map(s,0x800000,4096,3,&alias)<0);assert(chimera_x86_vm_map(s,0x0000800000000000ull,4096,4,&alias)<0);chimera_x86_vm_destroy(s);release(nullptr,boot,1);for(bool x:used)assert(!x);return 0;}