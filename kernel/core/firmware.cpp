#include "chimera/firmware.h"
#include "chimera/koronos_abi.h"
#include <stddef.h>
struct mb2_tag { uint32_t type,size; };
static uint64_t read64(const void *p){return *(const uint64_t*)p;}
extern "C" int chimera_firmware_probe(const void *boot_context, chimera_firmware_profile *out){
 if(!out)return -1; for(size_t i=0;i<sizeof(*out);++i)((uint8_t*)out)[i]=0; out->version=CHIMERA_FIRMWARE_VERSION;
 const koronos_boot_context *ctx=(const koronos_boot_context*)boot_context;
 if(!ctx||ctx->magic!=KORONOS_BOOTINFO_MAGIC||ctx->version!=KORONOS_ABI_VERSION)return -2;
 const uint8_t *base=(const uint8_t*)(uintptr_t)ctx->boot_info;
 if(!base)return -3;
 uint32_t total=*(const uint32_t*)base; uint32_t off=8;
 while(off+8<=total){
   const mb2_tag *t=(const mb2_tag*)(base+off); if(t->size<8||off+t->size>total)break;
   if(t->type==11||t->type==12){out->type=CHIMERA_FW_UEFI;out->efi_system_table=read64(base+off+8);out->runtime_services=1;}
   else if(t->type==14||t->type==15){out->acpi_rsdp=(uint64_t)(uintptr_t)(base+off+8);out->acpi_revision=(t->type==15)?2:1;}
   else if(t->type==13){out->smbios_entry=(uint64_t)(uintptr_t)(base+off+8);out->smbios_major=*(const uint8_t*)(base+off+8);out->smbios_minor=*(const uint8_t*)(base+off+9);}
   off=(off+t->size+7u)&~7u; if(t->type==0)break;
 }
 if(out->type==CHIMERA_FW_UNKNOWN)out->type=CHIMERA_FW_BIOS;
 return 0;
}
extern "C" int chimera_firmware_validate_tables(const chimera_firmware_profile *p){
 if(!p||p->version!=CHIMERA_FIRMWARE_VERSION)return -1;
 if(p->type==CHIMERA_FW_UEFI&&!p->efi_system_table)return -2;
 return 0;
}
