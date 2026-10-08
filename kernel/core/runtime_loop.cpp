#include <stdint.h>
#include "../include/chimera/scheduler.h"
#include "../include/chimera/multiboot_modules.h"
#include "../include/chimera/timer.h"
#include "../include/chimera/watchdog.h"
namespace {
static void vga_text(uint32_t row,uint32_t col,const char*text){volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;text[i]&&col+i<80;++i)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)text[i]);}
static void vga_hex(uint32_t row,uint32_t col,uint32_t value){static const char h[]="0123456789ABCDEF";volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;i<8&&col+i<80;++i)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)h[(value>>(28-4*i))&15u]);}
static void vga_clear_status_row(){volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t c=0;c<80;++c)v[24*80+c]=0x0720;}
static void vga_heartbeat(uint32_t sequence,uint32_t dispatched,uint32_t runnable){vga_clear_status_row();vga_text(24,0,"KORONOS SCHEDULER ALIVE");vga_hex(24,25,sequence);vga_text(24,34,"RUN");vga_hex(24,38,dispatched);vga_text(24,47,"READY");vga_hex(24,53,runnable);vga_text(24,62,"MB2");vga_hex(24,66,chimera_multiboot_module_count());}
}
extern "C" void koronos_idle_loop(void){
    uint32_t spin=0;
    for(;;){
        const uint32_t dispatched=chimera_sched_run_once(0);
        ++spin;
        chimera_watchdog_heartbeat(1u, chimera_timer_now() * 1000000ull);
        if((spin&0x0000FFFFu)==0)vga_heartbeat(spin,dispatched,chimera_sched_runnable_count());
#if defined(__x86_64__)||defined(__i386__)
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
