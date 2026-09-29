#include "chimera/firmware.h"
#include "chimera/koronos_abi.h"
#include <stddef.h>
extern "C" int chimera_firmware_probe(const void *boot_context, chimera_firmware_profile *out){
 if(!out)return -1; for(size_t i=0;i<sizeof(*out);++i)((uint8_t*)out)[i]=0; out->version=CHIMERA_FIRMWARE_VERSION;
 const koronos_boot_context *ctx=(const koronos_boot_context*)boot_context;
 if(ctx && ctx->magic==KORONOS_BOOTINFO_MAGIC && ctx->version==KORONOS_ABI_VERSION){const uint64_t *r=ctx->reserved;out->efi_system_table=r[0];out->acpi_rsdp=r[1];out->type=out->efi_system_table?CHIMERA_FW_UEFI:CHIMERA_FW_BIOS;out->runtime_services=out->efi_system_table?1:0;}
 return 0;
}
extern "C" int chimera_firmware_validate_tables(const chimera_firmware_profile *p){if(!p||p->version!=CHIMERA_FIRMWARE_VERSION)return -1;if(p->type==CHIMERA_FW_UEFI&&!p->efi_system_table)return -2;return 0;}
