#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "chimera/firmware.h"
#include "chimera/koronos_abi.h"

static void put32(uint8_t *p, uint32_t v) {
    p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); p[2]=(uint8_t)(v>>16); p[3]=(uint8_t)(v>>24);
}
static void put64(uint8_t *p, uint64_t v) {
    put32(p,(uint32_t)v); put32(p+4,(uint32_t)(v>>32));
}
static void tag(uint8_t *p, uint32_t type, uint32_t size) {
    put32(p,type); put32(p+4,size);
}
static int probe(uint8_t *block, uint32_t total, chimera_firmware_profile *out) {
    put32(block,total); put32(block+4,0);
    koronos_boot_context ctx{};
    ctx.magic=KORONOS_BOOTINFO_MAGIC; ctx.version=KORONOS_ABI_VERSION;
    ctx.boot_info=(uint64_t)(uintptr_t)block;
    return chimera_firmware_probe(&ctx,out);
}
int main() {
    alignas(8) uint8_t block[128]{};
    chimera_firmware_profile out{};

    /* Minimal valid Multiboot2 block, with a correctly sized end tag. */
    tag(block+8,0,8);
    assert(probe(block,16,&out)==0);
    assert(out.type==CHIMERA_FW_BIOS);
    assert(out.version==CHIMERA_FIRMWARE_VERSION);

    /* UEFI system-table tags require the complete pointer payload. */
    memset(block,0,sizeof(block));
    tag(block+8,11,16); put64(block+16,0x12345678);
    tag(block+24,0,8);
    assert(probe(block,32,&out)==0);
    assert(out.type==CHIMERA_FW_UEFI);
    assert(out.efi_system_table==0x12345678);

    /* ACPI v1/v2 tags must contain the fixed RSDP prefix. */
    memset(block,0,sizeof(block));
    tag(block+8,14,28);
    tag(block+40,0,8);
    assert(probe(block,48,&out)==0);
    assert(out.acpi_rsdp==(uint64_t)(uintptr_t)(block+16));
    assert(out.acpi_revision==1);

    memset(block,0,sizeof(block));
    tag(block+8,15,20); /* deliberately too short for the v2 RSDP */
    tag(block+32,0,8);
    assert(probe(block,40,&out)==-8);

    /* Reject a tag whose size escapes total_size and a missing end tag. */
    memset(block,0,sizeof(block));
    tag(block+8,11,64);
    assert(probe(block,32,&out)==-5);
    memset(block,0,sizeof(block));
    tag(block+8,11,16); put64(block+16,0x1000);
    assert(probe(block,24,&out)==-12);

    /* Reject undersized headers and impossible total_size values. */
    memset(block,0,sizeof(block));
    assert(probe(block,8,&out)==-4);
    tag(block+8,1,7);
    assert(probe(block,16,&out)==-5);
    return 0;
}
