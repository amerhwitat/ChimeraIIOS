#include "chimera/apic_topology.h"
namespace {
static uint32_t u32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}
}
extern "C" int koronos_apic_topology_parse_madt(const void *data,uint32_t length,
                                                  uint32_t bsp,koronos_apic_topology *out) {
    if(!data||!out||length>1024u*1024u)return -1;
    *out={};out->abi=KORONOS_APIC_TOPOLOGY_ABI;out->bsp_apic_id=bsp;out->bsp_index=UINT32_MAX;
    const auto *p=static_cast<const uint8_t*>(data);
    uint32_t offset=0;
    while(offset<length) {
        if(length-offset<2u)return -2;
        const uint8_t type=p[offset],size=p[offset+1];
        if(size<2u||size>length-offset)return -3;
        uint32_t id=0,uid=0,flags=0;bool cpu=false;uint8_t source=type;
        if(type==0u) {
            if(size!=8u)return -4;
            id=p[offset+3];uid=p[offset+2];flags=u32(p+offset+4);cpu=true;
        } else if(type==9u) {
            if(size!=16u)return -5;
            id=u32(p+offset+4);uid=u32(p+offset+12);flags=u32(p+offset+8);cpu=true;
            out->x2apic_present=1u;
        }
        if(cpu && (flags&3u)) {
            for(uint32_t i=0;i<out->count;i++)if(out->cpus[i].apic_id==id)return -6;
            if(out->count>=KORONOS_APIC_MAX_CPUS)return -7;
            koronos_apic_cpu &entry=out->cpus[out->count];
            entry.apic_id=id;entry.acpi_uid=uid;entry.flags=flags;
            entry.source_type=source;entry.enabled=(flags&1u)?1u:0u;
            if(entry.enabled)++out->enabled_count;
            if(id==bsp && entry.enabled)out->bsp_index=out->count;
            ++out->count;
        }
        offset+=size;
    }
    if(offset!=length)return -2;
    if(out->bsp_index==UINT32_MAX)return -8;
    return 0;
}
