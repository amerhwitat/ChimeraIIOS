#include "chimera/multiboot_modules.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void put32(uint8_t* p, uint32_t v) { memcpy(p, &v, sizeof(v)); }
static int check(bool ok, const char* name) {
    if (!ok) fprintf(stderr, "FAIL: %s\n", name);
    return ok ? 0 : 1;
}
static uint32_t build_valid(uint8_t* b, bool terminate_name, bool end_tag) {
    memset(b, 0, 256);
    uint32_t off = 8;
    const char* name = "chimera-live-initramfs.img";
    const uint32_t chars = static_cast<uint32_t>(strlen(name)) + (terminate_name ? 1u : 0u);
    const uint32_t size = 16u + chars;
    put32(b + off, 3); put32(b + off + 4, size);
    put32(b + off + 8, 0x1000); put32(b + off + 12, 0x2000);
    memcpy(b + off + 16, name, chars);
    off += (size + 7u) & ~7u;
    if (end_tag) { put32(b + off, 0); put32(b + off + 4, 8); off += 8; }
    put32(b, off); put32(b + 4, 0);
    return off;
}
int main() {
    alignas(8) uint8_t info[256];
    int failures = 0;
    build_valid(info, true, true);
    failures += check(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 1,
                      "valid module is enumerated");
    const chimera_boot_module* module = chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS);
    failures += check(module && module->base == 0x1000 && module->size == 0x1000,
                      "module bounds and classification are preserved");
    failures += check(module && memchr(module->cmdline, 0, sizeof(module->cmdline)) != nullptr,
                      "command line buffer is always terminated");

    build_valid(info, false, true);
    failures += check(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 1,
                      "unterminated source command line is bounded and accepted safely");
    module = chimera_multiboot_module(0);
    failures += check(module && memchr(module->cmdline, 0, sizeof(module->cmdline)) != nullptr,
                      "truncated command line remains terminated");

    build_valid(info, true, false);
    failures += check(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 0,
                      "missing Multiboot2 end tag rejects the information block");

    build_valid(info, true, true);
    put32(info + 8 + 4, 0xffffffffu);
    failures += check(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 0,
                      "oversized tag rejects the information block");

    build_valid(info, true, true);
    put32(info + 8 + 8, 0x2000); put32(info + 8 + 12, 0x1000);
    failures += check(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 0,
                      "invalid module address range is rejected");
    if (failures) return 1;
    puts("PASS: bounded Multiboot2 module parser tests");
    return 0;
}
