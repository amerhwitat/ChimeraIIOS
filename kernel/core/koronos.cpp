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
static void serial_hex32(uint32_t v) {
 static const char h[]="0123456789ABCDEF"; char s[9];
 for(int i=7;i>=0;--i){s[i]=h[v&15u];v>>=4;} s[8]=0; serial_write(s);
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
   serial_write("KORONOS: Multiboot2 module attached");
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
 if(!ctx || ctx->magic!=KORONOS_BOOTINFO_MAGIC || ctx->version!=KORONOS_ABI_VERSION) {
  koronos_state=0xBAD00001u; serial_write("KORONOS: invalid boot context"); return;
 }
 serial_write("KORONOS: Multiboot2 handoff accepted");
 koronos_report_multiboot_modules(ctx);
 koronos_arch_init(ctx);
 const struct koronos_cpu_features* f=koronos_get_cpu_features();
 serial_write("KORONOS: CPU vendor"); serial_write(f->vendor);
 serial_write("KORONOS: logical CPUs"); serial_hex32(f->logical_cpus);
 serial_write("KORONOS: VMX/SVM capability"); serial_hex32((uint32_t(f->vmx)<<1u)|uint32_t(f->svm));
 serial_write("KORONOS: Hypervisor present"); serial_hex32(f->hypervisor);
 chimera_sched_init(f->logical_cpus);
 chimera_learning_init(f->logical_cpus);
 chimera_register_virtio_drivers();
 chimera_register_display_drivers();
 chimera_driver_probe_all();
 chimera_learning_record(1, f->logical_cpus);
 koronos_elf64_init(); koronos_module_init();
 koronos_state=0x4B4F524Fu; serial_write("KORONOS_READY");
 serial_write("KORONOS: CPU online; entering scheduler idle loop");
}
