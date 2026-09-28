#include "../include/chimera/koronos_abi.h"
#include "chimera/scheduler.h"
#include "chimera/driver.h"
#include "chimera/learning.h"
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
static void vga_clear() {
 volatile uint16_t* v=(volatile uint16_t*)0xB8000;
 for(uint32_t i=0;i<80u*25u;i++) v[i]=0x0720;
}
static void vga_write(const char* s) {
 volatile uint16_t* v=(volatile uint16_t*)0xB8000;
 static uint32_t row=0,col=0;
 if(row==0 && col==0) vga_clear();
 if(!s)return;
 while(*s) {
  char c=*s++;
  if(c=='\r') { col=0; continue; }
  if(c=='\n') { col=0; if(++row>=25) row=24; continue; }
  if(col>=80) { col=0; if(++row>=25) row=24; }
  v[row*80+col++]=(uint16_t)(0x0F00u | (uint8_t)c);
 }
}
static void console_write(const char* s) { serial_write(s); vga_write(s); }
static void console_hex32(uint32_t v) {
 static const char h[]="0123456789ABCDEF"; char s[9];
 for(int i=7;i>=0;--i){s[i]=h[v&15u];v>>=4;} s[8]=0; console_write(s);
}
}
extern "C" void chimera_register_virtio_drivers(void);
extern "C" void chimera_register_display_drivers(void);

static void koronos_report_multiboot_modules(const koronos_boot_context* ctx) {
 if(!ctx || !ctx->boot_info) return;
 const uint8_t* base=(const uint8_t*)(uintptr_t)ctx->boot_info;
 const uint32_t total=*(const uint32_t*)base;
 if(total < 16 || total > 16u*1024u*1024u) return;
 uint64_t first_base=0, first_size=0;
 for(uint32_t off=8; off+8<=total;) {
  const uint32_t type=*(const uint32_t*)(base+off);
  const uint32_t size=*(const uint32_t*)(base+off+4);
  if(size<8 || off+size>total) break;
  if(type==3 && size>=16 && first_size==0) {
   first_base=*(const uint32_t*)(base+off+8);
   first_size=*(const uint32_t*)(base+off+12)-first_base;
   console_write("KORONOS: Multiboot2 module attached");
  }
  if(type==0) break;
  off=(off+size+7u)&~7u;
 }
 if(first_size) {
  koronos_boot_context* writable=const_cast<koronos_boot_context*>(ctx);
  writable->module_base=first_base;
  writable->module_size=first_size;
 }
}

extern "C" void koronos_boot(const koronos_boot_context* ctx) {
 serial_init();
 console_write("\nCHIMERA II OS / KORONOS\n");
 console_write("Boot handoff: ");
 if(!ctx || ctx->magic!=KORONOS_BOOTINFO_MAGIC || ctx->version!=KORONOS_ABI_VERSION) {
  koronos_state=0xBAD00001u; console_write("INVALID BOOT CONTEXT"); return;
 }
 console_write("OK");
 console_write("Initializing hardware...");
 koronos_report_multiboot_modules(ctx);
 koronos_arch_init(ctx);
 const struct koronos_cpu_features* f=koronos_get_cpu_features();
 console_write("CPU: "); console_write(f->vendor);
 console_write("Logical CPUs: "); console_hex32(f->logical_cpus);
 console_write("Hypervisor detected: "); console_hex32(f->hypervisor);
 console_write("Initializing scheduler...");
 chimera_sched_init(f->logical_cpus);
 chimera_learning_init(f->logical_cpus);
 console_write("Initializing virtual I/O drivers...");
 chimera_register_virtio_drivers();
 chimera_register_display_drivers();
 chimera_driver_probe_all();
 chimera_learning_record(1, f->logical_cpus);
 koronos_elf64_init(); koronos_module_init();
 koronos_state=0x4B4F524Fu;
 console_write("KORONOS READY");
 console_write("Console fallback: VGA text + COM1");
 console_write("If this screen is visible in VMware, kernel handoff succeeded.");
 console_write("Starting cooperative scheduler runtime...");
 console_write("Scheduler heartbeat will appear on VGA row 25.");
}
