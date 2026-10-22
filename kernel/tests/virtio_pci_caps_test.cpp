#include "chimera/virtio_pci.h"
#include <stdio.h>
#include <string.h>

static void put16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
static void put32(uint8_t *p, uint32_t v) { for (unsigned i=0;i<4;++i) p[i]=(uint8_t)(v>>(i*8)); }
static void cap(uint8_t *c, uint8_t at, uint8_t next, uint8_t type,
                uint8_t len, uint8_t bar, uint32_t off, uint32_t size) {
    c[at]=9; c[at+1]=next; c[at+2]=len; c[at+3]=type; c[at+4]=bar;
    put32(c+at+8,off); put32(c+at+12,size);
}
static int fail(const char *s) { fprintf(stderr,"FAIL: %s\n",s); return 1; }
int main() {
    uint8_t c[256] = {};
    koronos_virtio_pci_caps out{};
    put16(c,0x1af4); put16(c+2,0x1042); put16(c+6,1u<<4); c[0x34]=0x40;
    cap(c,0x40,0x50,1,16,0,0x1000,56);
    cap(c,0x50,0x64,2,20,2,0x2000,0x1000); put32(c+0x60,4);
    cap(c,0x64,0x74,3,16,1,0x3000,1);
    cap(c,0x74,0,4,16,0,0x4000,8);
    if(koronos_virtio_pci_parse_caps(c,&out)!=0) return fail("valid capability chain");
    if(!out.common.present || out.common.bar!=0 || out.common.offset!=0x1000 || out.common.length!=56) return fail("common region");
    if(!out.notify.present || out.notify.bar!=2 || out.notify.offset!=0x2000 || out.notify_multiplier!=4) return fail("notify region/multiplier");
    if(!out.isr.present || !out.device.present) return fail("ISR/device regions");

    uint8_t saved=c[0x50+2]; c[0x50+2]=16;
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("short notify capability rejected");
    c[0x50+2]=saved;
    c[0x50+1]=0x40;
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("cycle rejected");
    c[0x50+1]=0x64;
    c[0x40+1]=0x48;
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("overlapping capability pointer rejected");
    c[0x40+1]=0x50;
    put32(c+0x60,0);
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("zero notify multiplier rejected");
    put32(c+0x60,4);
    put32(c+0x58,0x1000);
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("overlapping BAR windows rejected");
    put32(c+0x58,0x2001);
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("misaligned notify window rejected");
    put32(c+0x58,0x2000);
    put16(c,0x1234);
    if(koronos_virtio_pci_parse_caps(c,&out)>=0) return fail("non-Virtio vendor rejected");
    puts("PASS: Virtio PCI capability parser validates function identity, chain bounds/cycles, region metadata, required capabilities and notify multiplier");
    return 0;
}
