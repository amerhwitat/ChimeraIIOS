#include "chimera/driver.h"
#include "chimera/device.h"
#include <stddef.h>
static chimera_driver_descriptor g_drivers[256];
static uint32_t g_count=0;
static int g_last_probe_count=0;
static int match(const chimera_driver_descriptor *d,const chimera_device *x){
 if(!d||!x)return 0;
 if(d->vendor_id!=0xFFFFu && d->vendor_id!=x->vendor_id)return 0;
 if(d->device_id!=0xFFFFu && d->device_id!=x->device_id)return 0;
 if(d->match_class && d->match_class!=x->class_code)return 0;
 if(d->match_subclass && d->match_subclass!=x->subclass)return 0;
 if(d->match_prog_if && d->match_prog_if!=x->prog_if)return 0;
 return 1;
}
extern "C" int chimera_driver_register(const chimera_driver_descriptor* d){
 if(!d||d->abi_version!=KORONOS_DRIVER_ABI||!d->name||g_count>=256)return -1;
 g_drivers[g_count++]=*d; return 0;
}
extern "C" const chimera_driver_registry* chimera_driver_registry_snapshot(){
 static chimera_driver_registry r{0,256,g_drivers}; r.count=g_count; return &r;
}
extern "C" int chimera_driver_start_all(){ int started=0; for(uint32_t i=0;i<g_count;i++){ chimera_driver_descriptor *d=&g_drivers[i]; if(d->state==2 || d->state==1){ if(d->probe && d->probe(0)!=0){d->state=5;continue;} d->state=3; started++; }} return started; }
extern "C" int chimera_driver_probe_all(){
 chimera_device_inventory inv{}; int n=chimera_hardware_enumerate_devices(&inv); if(n<0)return n;
 g_last_probe_count=0;
 for(uint32_t i=0;i<inv.count;i++){
   const chimera_device *x=&inv.devices[i]; int bound=0;
   for(uint32_t j=0;j<g_count;j++){
     chimera_driver_descriptor *d=&g_drivers[j];
     if(match(d,x)){ d->state=2; bound=1; g_last_probe_count++; if(d->probe)d->probe(x); break; }
   }
   if(!bound){
     // No native driver: keep the device visible for the compatibility manager.
     // Foreign .sys/.ko/.kext payloads are never executed in the Koronos ABI.
     static chimera_driver_descriptor compat[256]; static uint32_t cc=0;
     if(cc<256){
       chimera_driver_descriptor *d=&compat[cc++];
       *d={KORONOS_DRIVER_ABI,CHM_BUS_PCI,(x->device_class==CHM_DEV_NETWORK)?CHM_DRV_NET:
          (x->device_class==CHM_DEV_STORAGE)?CHM_DRV_STORAGE:
          (x->device_class==CHM_DEV_DISPLAY)?CHM_DRV_DISPLAY:
          (x->device_class==CHM_DEV_GPU)?CHM_DRV_GPU:CHM_DRV_USB,
          0,x->vendor_id,x->device_id,0,"compatibility-adapter","linux/windows catalog","1",
          x->class_code,x->subclass,x->prog_if,1,"compatibility-layer",0};
       chimera_driver_register(d);
     }
   }
 }
 return g_last_probe_count;
}
