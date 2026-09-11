#include <stdint.h>
#include "sf2_loader.h"

static uint32_t checksum32(const uint8_t *p, uint32_t n) {
    uint32_t h = 2166136261u;
    for (uint32_t i = 0; i < n; ++i) h = (h ^ p[i]) * 16777619u;
    return h;
}

void chm_sf2_entry(chm_bootinfo_t *bi) {
    if (!bi) for (;;) __asm__ volatile ("hlt");
    bi->magic = CHM_BOOTINFO_MAGIC;
    bi->version = CHM_BOOTINFO_VERSION;
    bi->size = (uint32_t)sizeof(*bi);
    bi->crc32 = checksum32((const uint8_t *)bi, 12);
    bi->flags |= CHM_BOOT_BIOS | CHM_BOOT_EXPERIMENTAL;
}

/* Called by the SF1 assembly handoff in a freestanding 64-bit build. */
void sf2_entry_asm(void) {
    static chm_bootinfo_t bootinfo;
    chm_sf2_entry(&bootinfo);
}
