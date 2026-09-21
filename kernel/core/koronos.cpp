#include "../include/chimera/koronos_abi.h"
namespace {
volatile uint32_t koronos_state=0;
static void serial_write8(uint8_t v) { *reinterpret_cast<volatile uint8_t*>(0x3F8)=v; }
static void serial_write(const char* s) { if(!s)return; while(*s)serial_write8((uint8_t)*s++); serial_write8('\r'); serial_write8('\n'); }
}
extern "C" void koronos_boot(const koronos_boot_context* ctx) {
 if(!ctx || ctx->magic!=KORONOS_BOOTINFO_MAGIC || ctx->version!=KORONOS_ABI_VERSION) {
  koronos_state=0xBAD00001u; serial_write("KORONOS: invalid boot context"); return;
 }
 koronos_arch_init(ctx); koronos_elf64_init(); koronos_module_init();
 koronos_state=0x4B4F524Fu; serial_write("KORONOS_READY");
}
