#include "chimera/frame_allocator.h"
#include "chimera/multiboot_modules.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

extern "C" uint32_t chimera_multiboot_module_count(void) { return 0; }
extern "C" const chimera_boot_module *chimera_multiboot_module(uint32_t) { return nullptr; }

static void put32(uint8_t *p, uint32_t v) { memcpy(p, &v, sizeof(v)); }
static void put64(uint8_t *p, uint64_t v) { memcpy(p, &v, sizeof(v)); }

static size_t make_info(uint8_t *b, bool above4g, bool framebuffer) {
    memset(b, 0, 256);
    size_t off = 8;
    put32(b + off, 6); put32(b + off + 4, above4g ? 64 : 40);
    put32(b + off + 8, 24); put32(b + off + 12, 0);
    put64(b + off + 16, 0x100000); put64(b + off + 24, 0x3f00000);
    put32(b + off + 32, 1); put32(b + off + 36, 0);
    if (above4g) {
        put64(b + off + 40, 0x100000000ull); put64(b + off + 48, 0x100000);
        put32(b + off + 56, 1); put32(b + off + 60, 0);
    }
    off += above4g ? 64 : 40;
    put32(b + off, 3); put32(b + off + 4, 20);
    put32(b + off + 8, 0x300000); put32(b + off + 12, 0x400000);
    memcpy(b + off + 16, "mod", 4);
    off += 24;
    if (framebuffer) {
        put32(b + off, 8); put32(b + off + 4, 32);
        put64(b + off + 8, 0x1000000);
        put32(b + off + 16, 1024); put32(b + off + 20, 1024);
        put32(b + off + 24, 768);
        b[off + 28] = 32; b[off + 29] = 1;
        off += 32;
    }
    put32(b + off, 0); put32(b + off + 4, 8); off += 8;
    put32(b, static_cast<uint32_t>(off));
    return off;
}

int main(int argc, char **argv) {
    uint8_t info[256];
    if (argc > 1 && strcmp(argv[1], "above4g") == 0) {
        make_info(info, true, false);
        assert(koronos_frame_allocator_init(reinterpret_cast<uint64_t>(info), 0x100000, 0x200000) == -2);
        assert(koronos_frame_free_count() == 0);
        puts("frame allocator: RAM above the 4-GiB bootstrap ceiling is rejected");
        return 0;
    }
    make_info(info, false, true);
    assert(koronos_frame_allocator_init(reinterpret_cast<uint64_t>(info), 0x100000, 0x200000) == 0);
    const uint64_t initial = koronos_frame_free_count();
    assert(initial > 1000);
    assert(koronos_frame_managed_limit() == 0x100000000ull);

    const uint64_t first = koronos_frame_alloc();
    assert(first == 0x200000);
    assert(koronos_frame_free_count() == initial - 1);
    assert(koronos_frame_free(first) == 0);
    assert(koronos_frame_free(first) == -2);
    assert(koronos_frame_free(first + 1) == -1);
    assert(koronos_frame_free(0x100000) == -2); // reserved kernel page is not owned by the allocator

    /* Module payloads must be reserved even if the bounded module registry
       did not enumerate them. */
    uint64_t address = 0;
    do {
        address = koronos_frame_alloc();
        assert(address != 0);
    } while (address < 0x400000);
    assert(address >= 0x400000);
    /* The framebuffer range must remain reserved despite usable-RAM overlap. */
    do {
        address = koronos_frame_alloc();
        assert(address != 0);
    } while (address < 0x1100000);
    assert(address >= 0x1100000);
    puts("frame allocator: ownership, double-free, alignment and framebuffer reservations passed");
    return 0;
}
