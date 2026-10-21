#include "chimera/device.h"
#include <stddef.h>
static chimera_device_inventory g_inv;
#if defined(__x86_64__) || defined(__i386__)
static inline void outl(uint16_t p,uint32_t v){__asm__ volatile("outl %0,%1"::"a"(v),"Nd"(p));}
static inline uint32_t inl(uint16_t p){uint32_t v;__asm__ volatile("inl %1,%0":"=a"(v):"Nd"(p));return v;}
static uint32_t pci_read(uint8_t bus,uint8_t dev,uint8_t fn,uint8_t off){
 uint32_t a=0x80000000u|((uint32_t)bus<<16)|((uint32_t)dev<<11)|((uint32_t)fn<<8)|(off&0xfcu); outl(0xCF8,a); return inl(0xCFC);
}
#endif
static chimera_device_class classify(uint8_t base,uint8_t sub){if(base==1)return CHM_DEV_STORAGE;if(base==2)return CHM_DEV_NETWORK;if(base==3)return sub==0x00?CHM_DEV_DISPLAY:CHM_DEV_GPU;if(base==6)return CHM_DEV_MOTHERBOARD; if(base==0x0C&&sub==3)return CHM_DEV_USB;return CHM_DEV_OTHER;}
extern "C" int chimera_hardware_device_class(uint8_t base,uint8_t sub){return (int)classify(base,sub);}

/* Decode address/type bits only. Resource sizing, reservation, mapping, and
 * device enablement are separate privileged operations and are not implied.
 */
extern "C" int chimera_pci_decode_bar(uint32_t low,uint32_t high,chimera_pci_bar *out){
 if(!out)return -1;
 out->address=0; out->kind=CHM_PCI_BAR_INVALID; out->prefetchable=0;
 out->consumes_next=0; out->reserved=0;
 if(low==0u || low==0xffffffffu)return -1;
 if(low&1u){
   out->kind=CHM_PCI_BAR_IO;
   out->address=(uint64_t)(low&~3u);
   return 0;
 }
 const uint32_t type=(low>>1)&3u;
 out->prefetchable=(uint8_t)((low>>3)&1u);
 if(type==0u){
   out->kind=CHM_PCI_BAR_MMIO32;
   out->address=(uint64_t)(low&0xfffffff0u);
   return 0;
 }
 if(type==1u){
   out->kind=CHM_PCI_BAR_MMIO20;
   out->address=(uint64_t)(low&0x000ffff0u);
   return 0;
 }
 if(type==2u){
   out->kind=CHM_PCI_BAR_MMIO64;
   out->address=((uint64_t)high<<32)|(uint64_t)(low&0xfffffff0u);
   out->consumes_next=1;
   return 0;
 }
 return -1; /* reserved memory BAR encoding */
}
extern "C" int chimera_hardware_enumerate_devices(chimera_device_inventory *out){
 if(!out)return -1;
 for(size_t i=0;i<sizeof(*out);++i)((uint8_t*)out)[i]=0;
#if defined(__x86_64__) || defined(__i386__)
 for(uint32_t bus=0;bus<256&&out->count<CHIMERA_DEVICE_MAX;++bus) for(uint32_t dev=0;dev<32&&out->count<CHIMERA_DEVICE_MAX;++dev) for(uint32_t fn=0;fn<8&&out->count<CHIMERA_DEVICE_MAX;++fn){
   uint32_t id=pci_read(bus,dev,fn,0); if(id==0xffffffffu||id==0u) continue;
   uint32_t classreg=pci_read(bus,dev,fn,8); uint32_t hdr=pci_read(bus,dev,fn,0x0c);
   chimera_device &d=out->devices[out->count++]; d.bus=1;d.bdf=(bus<<8)|(dev<<3)|fn;d.vendor_id=(uint16_t)(id&0xffff);d.device_id=(uint16_t)(id>>16);
   d.revision=classreg&0xff; d.prog_if=(classreg>>8)&0xff; d.subclass=(classreg>>16)&0xff; d.class_code=(classreg>>24)&0xff; d.flags=hdr;
   d.device_class=classify((uint8_t)d.class_code,(uint8_t)d.subclass);
   /* Header type 0 exposes six BARs; type 1 PCI bridges expose two. Read-only
    * discovery deliberately does not write all-ones to size BARs, enable bus
    * mastering, or dereference addresses. A later resource manager must size,
    * reserve and map these resources before a driver can use them.
    */
   const uint8_t header_type=(uint8_t)((hdr>>16)&0x7fu);
   d.bar_count=(header_type==0u)?6u:(header_type==1u?2u:0u);
   for(uint8_t bi=0;bi<d.bar_count;++bi)
     d.bar_raw[bi]=pci_read((uint8_t)bus,(uint8_t)dev,(uint8_t)fn,(uint8_t)(0x10u+4u*bi));
   d.name[0]='P';d.name[1]='C';d.name[2]='I';d.name[3]=0;
 }
#else
 out->count=0;
#endif
 g_inv=*out; return (int)out->count;
}
extern "C" const chimera_device_inventory *chimera_hardware_inventory(void){return &g_inv;}
