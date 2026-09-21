#include "../include/chimera/koronos_abi.h"
extern "C" void koronos_outb(uint16_t port,uint8_t value);
namespace {
volatile uint32_t koronos_state=0;
static uint8_t serial_in8(uint16_t port) { uint8_t v; __asm__ volatile("inb %1,%0" : "=a"(v) : "Nd"(port)); return v; }
static void serial_init() {
 koronos_outb(0x3F9,0); koronos_outb(0x3FB,0x80); koronos_outb(0x3F8,3); koronos_outb(0x3F9,0);
 koronos_outb(0x3FB,3); koronos_outb(0x3FA,0xC7); koronos_outb(0x3FC,3);
}
static void serial_write8(uint8_t v) { for(uint32_t i=0;i<100000u && !(serial_in8(0x3FD)&0x20);++i){} koronos_outb(0x3F8,v); }
static void serial_write(const char* s) { if(!s)return; while(*s)serial_write8((uint8_t)*s++); serial_write8('\r'); serial_write8('\n'); }
}
extern "C" void koronos_boot(const koronos_boot_context* ctx) {
 if(!ctx || ctx->magic!=KORONOS_BOOTINFO_MAGIC || ctx->version!=KORONOS_ABI_VERSION) {
  koronos_state=0xBAD00001u; serial_write("KORONOS: invalid boot context"); return;
 }
 serial_init(); serial_write("KORONOS: Multiboot2 handoff accepted");
 koronos_arch_init(ctx); koronos_elf64_init(); koronos_module_init();
 koronos_state=0x4B4F524Fu; serial_write("KORONOS_READY");
}