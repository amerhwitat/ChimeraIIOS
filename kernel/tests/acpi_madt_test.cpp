#include "chimera/acpi_madt.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

static void put32(uint8_t *p, uint32_t v) {
  p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); p[2]=(uint8_t)(v>>16); p[3]=(uint8_t)(v>>24);
}
static void put64(uint8_t *p, uint64_t v) { put32(p,(uint32_t)v); put32(p+4,(uint32_t)(v>>32)); }
static void checksum(uint8_t *p, uint32_t n, uint32_t off) {
  p[off]=0; uint8_t sum=0; for(uint32_t i=0;i<n;i++) sum=(uint8_t)(sum+p[i]); p[off]=(uint8_t)(0u-sum);
}
static uint32_t make_table(uint8_t *p) {
  memset(p,0,128); memcpy(p,"APIC",4); put32(p+36,0xfee00000); put32(p+40,1);
  uint32_t off=44;
  p[off]=0;p[off+1]=8;p[off+2]=0;p[off+3]=2;put32(p+off+4,1);off+=8;
  p[off]=0;p[off+1]=8;p[off+2]=1;p[off+3]=4;put32(p+off+4,2);off+=8;
  p[off]=9;p[off+1]=16;put32(p+off+4,0x123);put32(p+off+8,1);put32(p+off+12,2);off+=16;
  put32(p+4,off); checksum(p,off,9); return off;
}
int main() {
  uint8_t bytes[128]; koronos_acpi_topology topo{};
  uint32_t n=make_table(bytes);
  assert(koronos_acpi_madt_parse(bytes,n,&topo)==0);
  assert(topo.count==3 && topo.enabled_count==2 && topo.online_capable_count==0);
  assert(topo.local_apic_address==0xfee00000);
  assert(topo.cpus[0].apic_id==2 && topo.cpus[1].apic_id==4);
  assert(topo.cpus[2].x2apic==1 && topo.cpus[2].apic_id==0x123);
  assert(koronos_acpi_madt_parse(bytes,n-1,&topo)<0);
  bytes[0]='X'; assert(koronos_acpi_madt_parse(bytes,n,&topo)==-3);
  n=make_table(bytes); bytes[9] ^= 1; assert(koronos_acpi_madt_parse(bytes,n,&topo)==-5);
  n=make_table(bytes); bytes[45]=0; assert(koronos_acpi_madt_parse(bytes,n,&topo)==-7);
  n=make_table(bytes); bytes[45]=7; put32(bytes+48,1); checksum(bytes,n,9);
  /* Duplicate APIC IDs are rejected and output is cleared on failure. */
  assert(koronos_acpi_madt_parse(bytes,n,&topo)==-9 && topo.count==0);
  n=make_table(bytes); bytes[45]=7; put32(bytes+48,0); checksum(bytes,n,9);
  assert(koronos_acpi_madt_parse(bytes,n,&topo)==0);
  n=make_table(bytes); put64(bytes+48,0x100000000ull); /* not used in this layout */
  assert(koronos_acpi_madt_parse(bytes,n,&topo)<0);
  return 0;
}
