#include "../include/chimera/koronos_abi.h"
static volatile uint32_t arch_state;
extern "C" void koronos_arch_init(const koronos_boot_context* ctx) {
 if(!ctx)return;
 arch_state=(ctx->cpu_class<<16)|(ctx->cpu_mode&0xffffu);
}
