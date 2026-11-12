#include <stdint.h>
#include "../include/chimera/scheduler.h"
#include "../include/chimera/multiboot_modules.h"
extern "C" uint32_t koronos_monitor_task_id;

namespace {
static void vga_text(uint32_t row,uint32_t col,const char*text){volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;text[i]&&col+i<80;++i)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)text[i]);}
static void vga_hex(uint32_t row,uint32_t col,uint32_t value){static const char h[]="0123456789ABCDEF";volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;i<8&&col+i<80;++i)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)h[(value>>(28-4*i))&15u]);}
static void vga_clear_status_row(){volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t c=0;c<80;++c)v[24*80+c]=0x0720;}
static void vga_heartbeat(uint32_t sequence,uint32_t last_dispatch,uint32_t runnable){vga_clear_status_row();vga_text(24,0,"KORONOS CPU");vga_hex(24,12,chimera_sched_online_cpu_count());vga_text(24,20,"/");vga_hex(24,21,chimera_sched_cpu_count());vga_text(24,30,"LAST");vga_hex(24,35,last_dispatch);vga_text(24,44,"READY");vga_hex(24,50,runnable);vga_text(24,59,"MB2");vga_hex(24,63,chimera_multiboot_module_count());(void)sequence;}
}
extern "C" void koronos_idle_loop(void){
    uint32_t spin=0;
    for(;;){
        const uint32_t dispatched=chimera_sched_run_once(0);
        ++spin;
        /* Idle keep-alive: when every service is blocked there is no runnable
           work, so wake the monitor task on a fixed spin cadence. It prints one
           snapshot and blocks again, which makes runtime liveness observable
           instead of looking like a stalled kernel. */
        if(dispatched==0 && koronos_monitor_task_id!=0 && (spin&0x00FFFFFFu)==0)
            chimera_sched_wake(koronos_monitor_task_id);
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
