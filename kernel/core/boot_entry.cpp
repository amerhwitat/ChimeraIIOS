#include <stdint.h>
#include "../include/chimera/kernel_entry.h"
static volatile uint16_t *const vga=(uint16_t*)0xB8000;
static void put(const char *s){for(uint32_t i=0;s[i];++i)vga[i]=(uint16_t)s[i]|0x0700;}
extern "C" void koronos_boot_entry(const chm_bootinfo_t *bi){
    if(!bi || bi->magic!=CHM_BOOTINFO_MAGIC){put("KORONOS_BOOTINFO_INVALID"); for(;;)__asm__ volatile("hlt");}
    put("KORONOS_READY");
}
