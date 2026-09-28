#include <stdint.h>
#include "../include/chimera/scheduler.h"

namespace {
static inline void vga_heartbeat(uint32_t sequence) {
    volatile uint16_t* v=(volatile uint16_t*)0xB8000;
    const char* text="KORONOS SCHEDULER ALIVE ";
    for(uint32_t i=0;text[i] && i<24;i++)
        v[24u*80u+i]=(uint16_t)(0x0F00u|(uint8_t)text[i]);
    const char hex[]="0123456789ABCDEF";
    for(int i=0;i<8;i++)
        v[24u*80u+25u+(uint32_t)i]=(uint16_t)(0x0F00u|(uint8_t)hex[(sequence>>(28-4*i))&15u]);
}
}

extern "C" void koronos_idle_loop(void) {
    // This is the post-bootstrap scheduler pump, not a permanent HLT state.
    // Early Koronos has no interrupt-driven timer yet, so use a cooperative
    // polling loop until the timer/APIC service is brought online.
    uint32_t spin=0;
    for(;;) {
        (void)chimera_sched_run_once(0);
        if((++spin & 0x000FFFFFu)==0)
            vga_heartbeat(spin);
#if defined(__x86_64__) || defined(__i386__)
        __asm__ volatile("pause" ::: "memory");
#elif defined(__aarch64__)
        __asm__ volatile("yield" ::: "memory");
#elif defined(__riscv)
        __asm__ volatile("nop" ::: "memory");
#else
        __asm__ volatile("" ::: "memory");
#endif
    }
}
