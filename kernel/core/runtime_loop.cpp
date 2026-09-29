#include <stdint.h>
#include "../include/chimera/scheduler.h"
#include "../include/chimera/multiboot_modules.h"
namespace {
static void vga_text(uint32_t row,uint32_t col,const char* text){volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;text[i]&&col+i<80;i++)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)text[i]);}
static void vga_hex(uint32_t row,uint32_t col,uint32_t value){static const char h[]="0123456789ABCDEF";volatile uint16_t*v=(volatile uint16_t*)0xB8000;for(uint32_t i=0;i<8;i++)v[row*80+col+i]=(uint16_t)(0x0F00u|(uint8_t)h[(value>>(28-4*i))&15u]);}
static void vga_heartbeat(uint32_t sequence){vga_text(24,0,"KORONOS SCHEDULER ALIVE");vga_hex(24,25,sequence);vga_text(24,34,"TASKS");vga_hex(24,40,chimera_sched_runnable_count());vga_text(24,50,"MODULES");vga_hex(24,58,chimera_multiboot_module_count());}
}
extern "C" void koronos_idle_loop(void){
 uint32_t spin=0;
 for(;;){
  (void)chimera_sched_run_once(0);
  if((++spin&0x000FFFFFu)==0)vga_heartbeat(spin);
#if defined(__x86_64__)||defined(__i386__)
  __asm__ volatile("pause":::"memory");
#elif defined(__aarch64__)
  __asm__ volatile("yield":::"memory");
#elif defined(__riscv)
  __asm__ volatile("nop":::"memory");
#else
  __asm__ volatile("":::"memory");
#endif
 }
}
