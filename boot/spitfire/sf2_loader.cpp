#include <stdint.h>
#include "sf2_loader.h"
#include "../../kernel/include/chimera/koronos_abi.h"

static uint32_t checksum32(const uint8_t *p,uint32_t n){ uint32_t h=2166136261u; for(uint32_t i=0;i<n;++i) h=(h^p[i])*16777619u; return h; }

void chm_sf2_entry(chm_bootinfo_t *bi){
 if(!bi) for(;;)__asm__ volatile("hlt");
 bi->magic=CHM_BOOTINFO_MAGIC; bi->version=CHM_BOOTINFO_VERSION; bi->size=(uint32_t)sizeof(*bi);
 bi->crc32=checksum32((const uint8_t*)bi,12); bi->flags|=CHM_BOOT_BIOS|CHM_BOOT_EXPERIMENTAL;
}

static koronos_boot_context koronos_ctx;

/* SF1 enters long mode and calls this routine. Return value is placed in RAX and then RBX. */
extern "C" koronos_boot_context *sf2_entry_asm(void){
 static chm_bootinfo_t bootinfo;
 chm_sf2_entry(&bootinfo);
 koronos_ctx.magic=KORONOS_BOOTINFO_MAGIC;
 koronos_ctx.version=KORONOS_ABI_VERSION;
 koronos_ctx.boot_info=(uint64_t)(uintptr_t)&bootinfo;
 koronos_ctx.kernel_base=0x00100000ull;
 koronos_ctx.cpu_class=KORONOS_CPU_CISC;
 koronos_ctx.cpu_mode=KORONOS_X86_LONG64;
 koronos_ctx.module_base=0;
 koronos_ctx.module_size=0;
 return &koronos_ctx;
}