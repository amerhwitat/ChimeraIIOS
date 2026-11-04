#include "chimera/process_loader.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct TestContext {
    uint32_t create_calls;
    uint32_t map_calls;
    uint32_t destroy_calls;
    uint32_t fail_on_map;
    void *blocks[CHIMERA_ELF_LOADER_MAX_SEGMENTS + 1u];
};

static void put16(uint8_t *p, uint16_t v) { memcpy(p, &v, sizeof(v)); }
static void put32(uint8_t *p, uint32_t v) { memcpy(p, &v, sizeof(v)); }
static void put64(uint8_t *p, uint64_t v) { memcpy(p, &v, sizeof(v)); }

static void build_elf(uint8_t *b, size_t size, uint32_t flags, uint16_t phnum) {
    memset(b, 0, size);
    b[0] = 0x7f; b[1] = 'E'; b[2] = 'L'; b[3] = 'F';
    b[4] = 2; b[5] = 1; b[6] = 1;
    put16(b + 16, KORONOS_ET_EXEC);
    put16(b + 18, KORONOS_EM_X86_64);
    put32(b + 20, 1);
    put64(b + 24, 0x100400100ull);
    put64(b + 32, 64);
    put16(b + 52, 64);
    put16(b + 54, 56);
    put16(b + 56, phnum);
    uint8_t *ph = b + 64;
    put32(ph + 0, 1); put32(ph + 4, flags);
    put64(ph + 8, 0x100); put64(ph + 16, 0x100400100ull);
    put64(ph + 32, 4); put64(ph + 40, 0x1000); put64(ph + 48, 4096);
    b[0x100] = 0x90; b[0x101] = 0x91; b[0x102] = 0x92; b[0x103] = 0xc3;
    if (phnum > 1) {
        uint8_t *second = b + 64 + 56;
        put32(second + 0, 1); put32(second + 4, 5);
        put64(second + 8, 0x800); put64(second + 16, 0x100400800ull);
        put64(second + 32, 4); put64(second + 40, 0x1000); put64(second + 48, 4096);
        b[0x800] = 0x90;
    }
}

static void *create_as(void *opaque) { ++static_cast<TestContext *>(opaque)->create_calls; return opaque; }
static int map_pages(void *opaque, void *, uint64_t, uint64_t size,
                     uint32_t, void **alias) {
    TestContext *ctx = static_cast<TestContext *>(opaque);
    const uint32_t call = ++ctx->map_calls;
    if (ctx->fail_on_map == call) return -1;
    void *memory = calloc(1, static_cast<size_t>(size));
    if (!memory) return -1;
    ctx->blocks[call - 1u] = memory;
    *alias = memory;
    return 0;
}
static void destroy_as(void *opaque, void *) {
    TestContext *ctx = static_cast<TestContext *>(opaque);
    for (void *block : ctx->blocks) free(block);
    memset(ctx->blocks, 0, sizeof(ctx->blocks));
    ++ctx->destroy_calls;
}
static const chimera_elf_load_ops ops = {create_as, map_pages, destroy_as};

int main() {
    uint8_t image[4096];
    build_elf(image, sizeof(image), 5u, 1u);
    TestContext ctx{};
    chimera_loaded_elf loaded{};
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &ctx, &loaded) == 0);
    assert(loaded.abi == CHIMERA_ELF_LOADER_ABI);
    assert(loaded.segment_count == 1 && loaded.entry == 0x100400100ull);
    assert(loaded.image_low == 0x100400000ull && loaded.image_high == 0x100402000ull);
    assert(loaded.loaded_file_bytes == 4);
    const uint8_t *segment = static_cast<const uint8_t *>(ctx.blocks[0]);
    assert(segment[0x100] == 0x90 && segment[0x101] == 0x91 &&
           segment[0x102] == 0x92 && segment[0x103] == 0xc3);
    assert(segment[0] == 0 && segment[0x104] == 0);
    const uint8_t *stack = static_cast<const uint8_t *>(ctx.blocks[1]);
    assert(stack && stack[0] == 0);
    destroy_as(&ctx, loaded.address_space);
    assert(ctx.destroy_calls == 1);

    /* A failure mapping the first segment must also destroy the staged address space. */
    TestContext failed_segment{}; failed_segment.fail_on_map = 1;
    chimera_loaded_elf untouched{}; untouched.abi = 0xDEADBEEFu;
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &failed_segment, &untouched) == -14);
    assert(failed_segment.create_calls == 1 && failed_segment.destroy_calls == 1);
    assert(untouched.abi == 0xDEADBEEFu);

    /* A failure mapping the stack must destroy the staged image and leave out untouched. */
    TestContext failed{}; failed.fail_on_map = 2;
    chimera_loaded_elf sentinel{}; sentinel.abi = 0xDEADBEEFu;
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &failed, &sentinel) == -15);
    assert(failed.destroy_calls == 1 && failed.blocks[0] == nullptr);
    assert(sentinel.abi == 0xDEADBEEFu);

    /* A non-page-aligned stack is rejected before allocating an address space. */
    TestContext bad_stack{};
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4097, &ops, &bad_stack, &sentinel) == -5);
    assert(bad_stack.create_calls == 0 && bad_stack.map_calls == 0);

    /* W+X and page-rounded overlapping PT_LOAD segments fail before allocation. */
    build_elf(image, sizeof(image), 7u, 1u);
    TestContext wx{};
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &wx, &sentinel) == -6);
    assert(wx.map_calls == 0 && wx.destroy_calls == 0);

    build_elf(image, sizeof(image), 5u, 2u);
    TestContext overlap{};
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &overlap, &sentinel) == -12);
    assert(overlap.map_calls == 0 && overlap.destroy_calls == 0);

    /* Low addresses collide with the bootstrap identity mapping and are rejected. */
    build_elf(image, sizeof(image), 5u, 1u);
    put64(image + 24, 0x400100ull);
    put64(image + 64 + 16, 0x400000ull);
    TestContext low{};
    assert(chimera_elf_load_user_image(image, sizeof(image), KORONOS_EM_X86_64,
        0x100800000ull, 4096, &ops, &low, &sentinel) == -7);
    assert(low.map_calls == 0);

    puts("Koronos transactional ELF loader: mapping, BSS, stack, W^X, overlap and rollback passed");
    return 0;
}
