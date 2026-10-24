#include "../include/chimera/process.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static void put16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
static void put32(uint8_t *p, uint32_t v) { for (int i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i)); }
static void put64(uint8_t *p, uint64_t v) { for (int i=0;i<8;i++) p[i]=(uint8_t)(v>>(8*i)); }

static void build_elf(uint8_t *b, size_t n) {
    for (size_t i=0;i<n;i++) b[i]=0;
    b[0]=0x7f; b[1]='E'; b[2]='L'; b[3]='F'; b[4]=2; b[5]=1; b[6]=1;
    put16(b+16,KORONOS_ET_EXEC); put16(b+18,KORONOS_EM_X86_64);
    put32(b+20,1); put64(b+24,0x400100); put64(b+32,64);
    put16(b+52,64); put16(b+54,56); put16(b+56,1);
    put32(b+64,1); put32(b+68,5); put64(b+72,0x100);
    put64(b+80,0x400100); put64(b+96,4); put64(b+104,8192); put64(b+112,4096);
    b[0x100]=0x90; b[0x101]=0x90; b[0x102]=0x90; b[0x103]=0xc3;
}

int main() {
    uint8_t elf[512];
    build_elf(elf,sizeof(elf));
    assert(chimera_process_init()==0);
    uint32_t previous_pid=0;
    for (uint32_t i=0;i<CHIMERA_PROCESS_MAX+16u;i++) {
        chimera_process_image image{};
        const int pid=chimera_process_admit_elf(elf,sizeof(elf),KORONOS_EM_X86_64,0x700000,&image);
        assert(pid>0 && image.pid==(uint32_t)pid && image.state==CHIMERA_PROCESS_ADMITTED);
        assert((uint32_t)pid>previous_pid);
        previous_pid=(uint32_t)pid;
        assert(chimera_process_count()==1);
        assert(chimera_process_mark_resources_released((uint32_t)pid)==-4);
        assert(chimera_process_reap((uint32_t)pid)==-4);
        const chimera_process_state terminal=(i%2u)==0u ? CHIMERA_PROCESS_EXITED : CHIMERA_PROCESS_FAULTED;
        assert(chimera_process_set_state((uint32_t)pid,terminal)==0);
        assert(chimera_process_reap((uint32_t)pid)==-6);
        assert(chimera_process_mark_resources_released((uint32_t)pid)==0);
        assert(chimera_process_reap((uint32_t)pid)==0);
        assert(chimera_process_count()==0);
        assert(chimera_process_get((uint32_t)pid,&image)==-2);
        assert(chimera_process_reap((uint32_t)pid)==-2);
    }
    puts("process lifecycle: repeated admission, terminal-state gating, resource-release gating, reaping, slot reuse, and monotonic PID allocation passed");
    return 0;
}
