#include "../include/chimera/multiboot_modules.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

namespace {
struct Mb2Builder {
    alignas(8) uint8_t bytes[2048]{};
    uint32_t offset = 8;

    Mb2Builder() {
        put32(bytes, 0);
        put32(bytes + 4, 0);
    }

    static void put32(uint8_t *p, uint32_t v) {
        p[0] = (uint8_t)v;
        p[1] = (uint8_t)(v >> 8);
        p[2] = (uint8_t)(v >> 16);
        p[3] = (uint8_t)(v >> 24);
    }

    void module(const char *cmdline, uint32_t start) {
        const uint32_t text_size = (uint32_t)strlen(cmdline) + 1u;
        const uint32_t size = 16u + text_size;
        assert(offset + size + 16u < sizeof(bytes));
        put32(bytes + offset, 3u);
        put32(bytes + offset + 4u, size);
        put32(bytes + offset + 8u, start);
        put32(bytes + offset + 12u, start + 0x1000u);
        memcpy(bytes + offset + 16u, cmdline, text_size);
        offset = (offset + size + 7u) & ~7u;
    }

    uint64_t finish() {
        put32(bytes + offset, 0u);
        put32(bytes + offset + 4u, 8u);
        offset += 8u;
        put32(bytes, offset);
        return (uint64_t)(uintptr_t)bytes;
    }
};
}

int main() {
    Mb2Builder mb2;
    mb2.module("chimera-live-initramfs", 0x200000u);
    mb2.module("chimera-live-manifest", 0x202000u);
    mb2.module("chimera-installation-image", 0x204000u);
    mb2.module("chimera-installation-manifest", 0x206000u);
    mb2.module("chimera-installer-contract", 0x208000u);
    mb2.module("chimera-install-phases", 0x20A000u);
    mb2.module("chimera-installer-profiles", 0x20C000u);
    mb2.module("chimera-user-init-elf", 0x20E000u);
    mb2.module("chimera-recovery-initramfs", 0x210000u);
    mb2.module("chimera-recovery-manifest", 0x212000u);

    const uint32_t count = chimera_multiboot_scan(mb2.finish());
    assert(count == 10u);
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS));
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_MANIFEST));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_MANIFEST));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_CONTRACT));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PHASES));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PROFILES));
    assert(chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF));
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS));
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST));
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS)->kind ==
           CHIMERA_MODULE_RECOVERY_INITRAMFS);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST)->kind ==
           CHIMERA_MODULE_RECOVERY_MANIFEST);

    puts("Koronos Multiboot2 target classification: live, installer, user-init and recovery modules passed");
    return 0;
}
