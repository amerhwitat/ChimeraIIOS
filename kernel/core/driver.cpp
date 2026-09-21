#include "chimera/driver.h"
#include <stddef.h>
static chimera_driver_descriptor g_drivers[256];
static uint32_t g_count=0;
extern "C" int chimera_driver_register(const chimera_driver_descriptor* d){
  if(!d || d->abi_version!=KORONOS_DRIVER_ABI || !d->name || g_count>=256) return -1;
  g_drivers[g_count++]=*d; return 0;
}
extern "C" const chimera_driver_registry* chimera_driver_registry_snapshot(){
  static chimera_driver_registry r{0,256,g_drivers}; r.count=g_count; return &r;
}
extern "C" int chimera_driver_probe_all(){
  // Hardware-specific probing is dispatched by bus drivers. The registry itself
  // is deterministic and safe before device enumeration is initialized.
  return (int)g_count;
}
