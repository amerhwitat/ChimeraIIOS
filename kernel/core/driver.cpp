#include "chimera/driver.h"
#include "chimera/device.h"
#include <stddef.h>
static chimera_driver_descriptor g_drivers[256];
static uint32_t g_count = 0;
static int score_match(const chimera_driver_descriptor* d, const chimera_device* x, uint32_t bus) {
 if (!d || !x || d->abi_version != KORONOS_DRIVER_ABI || d->bus != bus) return -1;
 int score = 0;
 if (d->vendor_id != 0xFFFFu) { if (d->vendor_id != x->vendor_id) return -1; score += 100; }
 if (d->device_id != 0xFFFFu) { if (d->device_id != x->device_id) return -1; score += 100; }
 if (d->subsystem_id != 0u) { const uint32_t subsystem = ((uint32_t)x->subsystem_vendor << 16) | x->subsystem_device; if (d->subsystem_id != subsystem) return -1; score += 40; }
 /* 0xff is the wildcard; zero is a valid PCI class/subclass/programming-interface value. */
 if (d->match_class != 0xffu) { if (d->match_class != (uint8_t)x->class_code) return -1; score += 30; }
 if (d->match_subclass != 0xffu) { if (d->match_subclass != (uint8_t)x->subclass) return -1; score += 20; }
 if (d->match_prog_if != 0xffu) { if (d->match_prog_if != (uint8_t)x->prog_if) return -1; score += 10; }
 return score;
}
extern "C" int chimera_driver_register(const chimera_driver_descriptor* d) {
 if (!d || d->abi_version != KORONOS_DRIVER_ABI || !d->name || g_count >= 256) return -1;
 for (uint32_t i=0;i<g_count;++i) if (g_drivers[i].bus==d->bus && g_drivers[i].vendor_id==d->vendor_id && g_drivers[i].device_id==d->device_id && g_drivers[i].subsystem_id==d->subsystem_id && g_drivers[i].match_class==d->match_class && g_drivers[i].match_subclass==d->match_subclass && g_drivers[i].match_prog_if==d->match_prog_if) return -2;
 g_drivers[g_count]=*d; if (g_drivers[g_count].state>5u) g_drivers[g_count].state=0; ++g_count; return 0;
}
extern "C" const chimera_driver_registry* chimera_driver_registry_snapshot(void) { static chimera_driver_registry r{0,256,g_drivers}; r.count=g_count; return &r; }
extern "C" const chimera_driver_descriptor* chimera_driver_best_match(const void* device, uint32_t bus) {
 const chimera_device* x=static_cast<const chimera_device*>(device); if(!x)return 0; int best_score=-1; const chimera_driver_descriptor* best=0;
 for(uint32_t i=0;i<g_count;++i){ int score=score_match(&g_drivers[i],x,bus); if(score>best_score){best_score=score;best=&g_drivers[i];} }
 return best;
}
extern "C" int chimera_driver_start_all(void) { int started=0; for(uint32_t i=0;i<g_count;++i){chimera_driver_descriptor* d=&g_drivers[i]; if(d->state==2u||d->state==1u){if(!d->probe){d->state=2u;continue;} if(d->probe(0)!=0){d->state=5u;continue;} d->state=3u;++started;}} return started; }
extern "C" int chimera_driver_probe_all(void) {
 chimera_device_inventory inv{}; int n=chimera_hardware_enumerate_devices(&inv); if(n<0)return n;
 int matched=0; for(uint32_t i=0;i<inv.count;++i){const chimera_device* x=&inv.devices[i]; const chimera_driver_descriptor* candidate=chimera_driver_best_match(x,x->bus); if(!candidate)continue; chimera_driver_descriptor* selected=0;
  for(uint32_t j=0;j<g_count;++j)if(&g_drivers[j]==candidate){selected=&g_drivers[j];break;} if(!selected)continue;
  selected->state=2u; ++matched; /* A metadata match is not a successful hardware initialization. */
  if(selected->probe){if(selected->probe(x)==0)selected->state=3u;else selected->state=5u;}
 }
 return matched;
}
