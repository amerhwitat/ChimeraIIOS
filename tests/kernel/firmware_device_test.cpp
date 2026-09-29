#include "chimera/firmware.h"
#include "chimera/device.h"
#include "chimera/koronos_abi.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
struct Tag { uint32_t type,size; };
int main(){
  alignas(8) uint8_t mb[64]{};
  *(uint32_t*)mb=32; *(uint32_t*)(mb+4)=0;
  Tag *acpi=(Tag*)(mb+8); acpi->type=14; acpi->size=16;
  *(uint64_t*)(mb+16)=0x12345000ull;
  Tag *end=(Tag*)(mb+24); end->type=0; end->size=8;
  koronos_boot_context ctx{}; ctx.magic=KORONOS_BOOTINFO_MAGIC; ctx.version=KORONOS_ABI_VERSION; ctx.boot_info=(uint64_t)(uintptr_t)mb;
  chimera_firmware_profile fw{};
  assert(chimera_firmware_probe(&ctx,&fw)==0);
  assert(fw.type==CHIMERA_FW_BIOS);
  assert(fw.acpi_rsdp!=0);
  assert(chimera_hardware_device_class(1,6)==CHM_DEV_STORAGE);
  assert(chimera_hardware_device_class(2,0)==CHM_DEV_NETWORK);
  assert(chimera_hardware_device_class(3,0)==CHM_DEV_DISPLAY);
  assert(chimera_hardware_device_class(3,2)==CHM_DEV_GPU);
  assert(chimera_hardware_device_class(6,0)==CHM_DEV_MOTHERBOARD);
  puts("firmware/device identity tests passed");
  return 0;
}
