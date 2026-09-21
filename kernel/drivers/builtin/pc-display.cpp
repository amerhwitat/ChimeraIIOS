#include "chimera/driver.h"
static const chimera_driver_descriptor vga{KORONOS_DRIVER_ABI,CHM_BUS_PCI,CHM_DRV_DISPLAY,0,0xFFFF,0xFFFF,0,"generic-vga","vga","1"};
extern "C" void chimera_register_display_drivers(){ chimera_driver_register(&vga); }
