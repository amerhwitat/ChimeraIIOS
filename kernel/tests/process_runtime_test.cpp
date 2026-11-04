#include "chimera/process.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

struct Region { uint64_t base=0,size=0; uint32_t flags=0; uint8_t bytes[16384]{}; };
struct Mock { Region regions[4]{}; uint32_t count=0; bool destroyed=false; };
static void *create_as(void *p) { auto *m=(Mock*)p; m->count=0; m->destroyed=false; return m; }
static int map_pages(void *p,void *as,uint64_t base,uint64_t size,uint32_t flags,void **alias) {
    auto *m=(Mock*)p;
    if(as!=p||!alias||m->count>=4||size>sizeof(m->regions[0].bytes)) return -1;
    for(uint32_t i=0;i<m->count;i++)
        if(base<m->regions[i].base+m->regions[i].size&&m->regions[i].base<base+size) return -2;
    auto &r=m->regions[m->count++]; r.base=base; r.size=size; r.flags=flags; *alias=r.bytes; return 0;
}
static void destroy_as(void *p,void *as) { assert(p==as); ((Mock*)p)->destroyed=true; }
static void put16(uint8_t*p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void put32(uint8_t*p,uint32_t v){for(int i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static void put64(uint8_t*p,uint64_t v){for(int i=0;i<8;i++)p[i]=(uint8_t)(v>>(8*i));}
static void build_elf(uint8_t*b,size_t n){
    for(size_t i=0;i<n;i++)b[i]=0;
    b[0]=0x7f;b[1]='E';b[2]='L';b[3]='F';b[4]=2;b[5]=1;b[6]=1;
    put16(b+16,KORONOS_ET_EXEC);put16(b+18,KORONOS_EM_X86_64);put32(b+20,1);
    put64(b+24,0x100400100);put64(b+32,64);
    put16(b+52,64);put16(b+54,56);put16(b+56,1);
    put32(b+64,1);put32(b+68,5);put64(b+72,0x1000);
    put64(b+80,0x100400000);put64(b+96,16);put64(b+104,8192);put64(b+112,4096);
    for(int i=0;i<16;i++)b[0x1000+i]=0x90;
}
int main(){
    uint8_t image[8192]{};build_elf(image,sizeof(image));
    chimera_process_init();
    chimera_process_image admitted{};
    const int pid=chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x100800000,&admitted);
    assert(pid>0&&admitted.state==CHIMERA_PROCESS_ADMITTED);
    chimera_elf_load_ops ops{create_as,map_pages,destroy_as};Mock mock{};
    assert(chimera_process_load_elf((uint32_t)pid,image,sizeof(image),KORONOS_EM_X86_64,
                                    0x100800000,8192,&ops,&mock)==0);
    chimera_process_runtime runtime{};
    assert(chimera_process_get_runtime((uint32_t)pid,&runtime)==0);
    assert(runtime.abi==CHIMERA_PROCESS_RUNTIME_ABI&&runtime.loaded==1);
    assert(runtime.address_space==&mock&&runtime.entry==0x100400100);
    assert(runtime.user_stack_top==0x100800000&&runtime.execution_context_ready==0);
    chimera_process_image snapshot{};
    assert(chimera_process_get((uint32_t)pid,&snapshot)==0);
    assert(snapshot.state==CHIMERA_PROCESS_ADMITTED); // mapped is not runnable
    assert(chimera_process_set_state((uint32_t)pid,CHIMERA_PROCESS_READY)==-3);
    assert(chimera_process_get_runtime((uint32_t)pid,&runtime)==0);
    assert(runtime.execution_context_ready==0&&runtime.saved_kernel_rsp==0);
    assert(chimera_process_release((uint32_t)pid)==0&&mock.destroyed);
    assert(chimera_process_count()==0);
    puts("process runtime: process-owned address-space load, explicit not-runnable boundary, and teardown passed");
    return 0;
}
