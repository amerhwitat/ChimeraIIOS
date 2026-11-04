#include "chimera/apic_topology.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
static void put32(uint8_t*p,uint32_t v){p[0]=v&255;p[1]=(v>>8)&255;p[2]=(v>>16)&255;p[3]=(v>>24)&255;}
int main(){
 uint8_t madt[24]={};
 // Type 0: enabled BSP APIC 2, ACPI UID 0.
 madt[0]=0;madt[1]=8;madt[2]=0;madt[3]=2;put32(madt+4,1);
 // Type 9: enabled x2APIC APIC 0x102, UID 1.
 madt[8]=9;madt[9]=16;put32(madt+12,0x102);put32(madt+16,1);put32(madt+20,1);
 koronos_apic_topology t{};
 assert(koronos_apic_topology_parse_madt(madt,sizeof(madt),2,&t)==0);
 assert(t.abi==KORONOS_APIC_TOPOLOGY_ABI&&t.count==2&&t.enabled_count==2);
 assert(t.bsp_index==0&&t.bsp_apic_id==2&&t.x2apic_present==1);
 assert(t.cpus[1].apic_id==0x102&&t.cpus[1].source_type==9);
 assert(koronos_apic_topology_parse_madt(madt,7,2,&t)<0); // truncated legacy record
 assert(koronos_apic_topology_parse_madt(madt,sizeof(madt),99,&t)==-8); // no BSP
 uint8_t bad[8]={0,1,0,0,0,0,0,0};
 assert(koronos_apic_topology_parse_madt(bad,sizeof(bad),0,&t)==-3);
 uint8_t dup[16]={0,8,0,2,1,0,0,0,0,8,1,2,1,0,0,0};
 assert(koronos_apic_topology_parse_madt(dup,sizeof(dup),2,&t)==-6);
 return 0;
}
