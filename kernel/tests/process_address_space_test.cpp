#include "chimera/process.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern "C" int koronos_process_fd_init(void) { return 0; }
extern "C" int koronos_process_fd_close_all(uint32_t) { return 0; }

static void put16(uint8_t *p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void put32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static void put64(uint8_t *p,uint64_t v){for(unsigned i=0;i<8;i++)p[i]=(uint8_t)(v>>(8*i));}
static void make_elf(uint8_t *b,size_t n){
 memset(b,0,n); b[0]=0x7f;b[1]='E';b[2]='L';b[3]='F';b[4]=2;b[5]=1;b[6]=1;
 put16(b+16,KORONOS_ET_EXEC);put16(b+18,KORONOS_EM_X86_64);put32(b+20,1);
 put64(b+24,0x100400100);put64(b+32,64);put16(b+52,64);put16(b+54,56);put16(b+56,1);
 put32(b+64,1);put32(b+68,5);put64(b+72,0x100);put64(b+80,0x100400100);
 put64(b+96,4);put64(b+104,8192);put64(b+112,4096);b[0x100]=0x90;
}
int main(){
 uint8_t elf[512];make_elf(elf,sizeof(elf));
 assert(chimera_process_init()==0);
 chimera_process_image admitted{};
 int pid=chimera_process_admit_elf(elf,sizeof(elf),KORONOS_EM_X86_64,0x100700000,&admitted);
 assert(pid>0&&admitted.address_space_root==0&&admitted.state==CHIMERA_PROCESS_ADMITTED);
 assert(chimera_process_bind_address_space((uint32_t)pid,0)==-1);
 assert(chimera_process_bind_address_space((uint32_t)pid,0x12345001)==-1);
 assert(chimera_process_bind_address_space((uint32_t)pid,0x12345000)==0);
 assert(chimera_process_bind_address_space((uint32_t)pid,0x22345000)==-3);
 chimera_process_image current{};
 assert(chimera_process_get((uint32_t)pid,&current)==0);
 assert(current.address_space_root==0x12345000);
 assert(chimera_process_set_state((uint32_t)pid,CHIMERA_PROCESS_RUNNING)==0);
 assert(chimera_process_bind_address_space((uint32_t)pid,0x32345000)==-3);
 assert(chimera_process_reap((uint32_t)pid,nullptr)==-3);
 assert(chimera_process_set_state((uint32_t)pid,CHIMERA_PROCESS_EXITED)==0);
 assert(chimera_process_reap((uint32_t)pid,nullptr)==0);
 assert(chimera_process_get((uint32_t)pid,&current)==-2);
 assert(chimera_process_count()==0);
 puts("process address-space ownership: alignment, one-time bind, state and reap guards passed");
 return 0;
}
