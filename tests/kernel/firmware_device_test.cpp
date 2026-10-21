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
  chimera_pci_bar bar{};
  assert(chimera_pci_decode_bar(0,0,&bar)!=0 && bar.kind==CHM_PCI_BAR_INVALID);
  assert(chimera_pci_decode_bar(0x0000c001u,0,&bar)==0);
  assert(bar.kind==CHM_PCI_BAR_IO && bar.address==0x0000c000u);
  assert(chimera_pci_decode_bar(0xFEBF0008u,0,&bar)==0);
  assert(bar.kind==CHM_PCI_BAR_MMIO32 && bar.address==0xFEBF0000u && bar.prefetchable==1);
  assert(chimera_pci_decode_bar(0x000c0004u,0x00000012u,&bar)==0);
  assert(bar.kind==CHM_PCI_BAR_MMIO64 && bar.address==0x00000012000c0000ull && bar.consumes_next==1);
  assert(chimera_pci_decode_bar(0x00000006u,0,&bar)!=0 && bar.kind==CHM_PCI_BAR_INVALID);
  chimera_device captured{}; captured.bar_count=3;
  captured.bar_raw[0]=0x000c0004u; captured.bar_raw[1]=0x00000012u; captured.bar_raw[2]=0x0000c001u;
  assert(chimera_pci_decode_device_bar(&captured,0,&bar)==0 && bar.kind==CHM_PCI_BAR_MMIO64 && bar.address==0x00000012000c0000ull);
  assert(chimera_pci_decode_device_bar(&captured,2,&bar)==0 && bar.kind==CHM_PCI_BAR_IO && bar.address==0x0000c000u);
  assert(chimera_pci_decode_device_bar(&captured,3,&bar)!=0 && bar.kind==CHM_PCI_BAR_INVALID);
  captured.bar_count=1;
  assert(chimera_pci_decode_device_bar(&captured,0,&bar)!=0 && bar.kind==CHM_PCI_BAR_INVALID);
  puts("firmware/device identity tests passed");
  return 0;
}
