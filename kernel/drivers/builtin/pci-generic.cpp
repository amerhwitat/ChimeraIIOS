#include "chimera/driver.h"
static chimera_driver_descriptor pci_storage{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_STORAGE,0,0xFFFF,0xFFFF,0,"pci-storage-generic","kernel","1",1,0,0,0,"native",0};
static chimera_driver_descriptor pci_network{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_NET,0,0xFFFF,0xFFFF,0,"pci-network-generic","kernel","1",2,0,0,0,"native",0};
static chimera_driver_descriptor pci_display{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_DISPLAY,0,0xFFFF,0xFFFF,0,"pci-display-generic","kernel","1",3,0,0,0,"native",0};
static chimera_driver_descriptor pci_platform{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_PLATFORM,0,0xFFFF,0xFFFF,0,"pci-platform-generic","acpi/smbios","1",6,0,0,0,"native",0};
static chimera_driver_descriptor pci_gpu{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_GPU,0,0xFFFF,0xFFFF,0,"pci-gpu-generic","kernel","1",3,0,0,0,"native",0};
extern "C" void chimera_register_pci_generic_drivers(){chimera_driver_register(&pci_storage);chimera_driver_register(&pci_network);chimera_driver_register(&pci_display);chimera_driver_register(&pci_gpu);chimera_driver_register(&pci_platform);}
