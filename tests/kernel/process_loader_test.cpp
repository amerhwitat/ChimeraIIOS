#include "../../kernel/include/chimera/process_loader.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <memory>
#include <vector>

namespace {
struct Mapping {
    uint64_t base;
    uint64_t size;
    uint32_t flags;
    std::unique_ptr<uint8_t[]> bytes;
};
struct AddressSpace {
    std::vector<Mapping> mappings;
};
struct FakeMmu {
    unsigned create_calls = 0;
    unsigned destroy_calls = 0;
    unsigned map_calls = 0;
    unsigned fail_map_call = 0;
};
static void put16(uint8_t *p, uint16_t v) {
    p[0] = static_cast<uint8_t>(v);
    p[1] = static_cast<uint8_t>(v >> 8);
}
static void put32(uint8_t *p, uint32_t v) {
    for (int i = 0; i < 4; ++i) p[i] = static_cast<uint8_t>(v >> (8 * i));
}
static void put64(uint8_t *p, uint64_t v) {
    for (int i = 0; i < 8; ++i) p[i] = static_cast<uint8_t>(v >> (8 * i));
}
static void build_elf(uint8_t *b, size_t n, uint32_t flags = 5,
                      uint64_t memsz = 0x2000) {
    memset(b, 0, n);
    b[0] = 0x7f; b[1] = 'E'; b[2] = 'L'; b[3] = 'F';
    b[4] = 2; b[5] = 1; b[6] = 1;
    put16(b + 16, KORONOS_ET_EXEC);
    put16(b + 18, KORONOS_EM_X86_64);
    put32(b + 20, 1);
    put64(b + 24, 0x400100);
    put64(b + 32, 64);
    put16(b + 52, 64);
    put16(b + 54, 56);
    put16(b + 56, 1);
    put32(b + 64, 1);       // PT_LOAD
    put32(b + 68, flags);   // PF_R | PF_X by default
    put64(b + 72, 0x100);   // file offset
    put64(b + 80, 0x400100);
    put64(b + 96, 4);       // file-backed bytes
    put64(b + 104, memsz);  // memory size, including BSS
    put64(b + 112, 4096);
    b[0x100] = 0x90; b[0x101] = 0x90; b[0x102] = 0x90; b[0x103] = 0xc3;
}
static void *create_as(void *opaque) {
    auto *mmu = static_cast<FakeMmu *>(opaque);
    ++mmu->create_calls;
    return new AddressSpace{};
}
static int map_pages(void *opaque, void *as_opaque, uint64_t base,
                     uint64_t size, uint32_t flags, void **alias) {
    auto *mmu = static_cast<FakeMmu *>(opaque);
    auto *as = static_cast<AddressSpace *>(as_opaque);
    ++mmu->map_calls;
    *alias = nullptr;
    if (mmu->fail_map_call == mmu->map_calls || size == 0 ||
        size > 16 * 1024 * 1024) return -1;
    Mapping m{base, size, flags, std::make_unique<uint8_t[]>(static_cast<size_t>(size))};
    memset(m.bytes.get(), 0xA5, static_cast<size_t>(size));
    *alias = m.bytes.get();
    as->mappings.push_back(std::move(m));
    return 0;
}
static void destroy_as(void *opaque, void *as_opaque) {
    ++static_cast<FakeMmu *>(opaque)->destroy_calls;
    delete static_cast<AddressSpace *>(as_opaque);
}
static const chimera_elf_load_ops ops{create_as, map_pages, destroy_as};

static void test_load_copies_bytes_zeroes_bss_and_maps_stack() {
    uint8_t elf[512];
    build_elf(elf, sizeof(elf));
    FakeMmu mmu{};
    chimera_loaded_elf loaded{};
    const int rc = chimera_elf_load_user_image(
        elf, sizeof(elf), KORONOS_EM_X86_64, 0x800000, 8192, &ops, &mmu, &loaded);
    assert(rc == 0);
    assert(loaded.abi == CHIMERA_ELF_LOADER_ABI);
    assert(loaded.segment_count == 1 && loaded.entry == 0x400100);
    assert(loaded.user_stack_top == 0x800000 && loaded.address_space != nullptr);
    assert(mmu.create_calls == 1 && mmu.destroy_calls == 0);
    auto *as = static_cast<AddressSpace *>(loaded.address_space);
    assert(as->mappings.size() == 2);
    const Mapping &segment = as->mappings[0];
    assert(segment.base == 0x400000 && segment.flags == 5);
    assert(segment.bytes[0x100] == 0x90 && segment.bytes[0x103] == 0xc3);
    for (size_t i = 0; i < segment.size; ++i) {
        if (i >= 0x100 && i < 0x104) continue;
        assert(segment.bytes[i] == 0); // includes zeroed BSS and page padding
    }
    const Mapping &stack = as->mappings[1];
    assert(stack.base == 0x7fe000 && stack.size == 8192);
    assert((stack.flags & 2u) != 0 && (stack.flags & 1u) == 0);
    for (size_t i = 0; i < stack.size; ++i) assert(stack.bytes[i] == 0);
    destroy_as(&mmu, loaded.address_space);
    assert(mmu.destroy_calls == 1);
}

static void test_rejects_writable_executable_segment_before_mapping() {
    uint8_t elf[512];
    build_elf(elf, sizeof(elf), 7);
    FakeMmu mmu{};
    chimera_loaded_elf loaded{};
    assert(chimera_elf_load_user_image(
        elf, sizeof(elf), KORONOS_EM_X86_64, 0x800000, 8192, &ops, &mmu, &loaded) == -6);
    assert(mmu.create_calls == 0 && mmu.map_calls == 0 && mmu.destroy_calls == 0);
}

static void test_mapping_failure_destroys_partial_address_space() {
    uint8_t elf[512];
    build_elf(elf, sizeof(elf));
    FakeMmu mmu{};
    mmu.fail_map_call = 2; // segment mapping succeeds; stack mapping fails
    chimera_loaded_elf loaded{};
    assert(chimera_elf_load_user_image(
        elf, sizeof(elf), KORONOS_EM_X86_64, 0x800000, 8192, &ops, &mmu, &loaded) == -15);
    assert(mmu.create_calls == 1 && mmu.map_calls == 2 && mmu.destroy_calls == 1);
}

static void test_rejects_entry_outside_executable_segment() {
    uint8_t elf[512];
    build_elf(elf, sizeof(elf));
    put64(elf + 24, 0x500000);
    FakeMmu mmu{};
    chimera_loaded_elf loaded{};
    assert(chimera_elf_load_user_image(
        elf, sizeof(elf), KORONOS_EM_X86_64, 0x800000, 8192, &ops, &mmu, &loaded) == -10);
    assert(mmu.create_calls == 0 && mmu.map_calls == 0);
}
}

int main() {
    test_load_copies_bytes_zeroes_bss_and_maps_stack();
    test_rejects_writable_executable_segment_before_mapping();
    test_mapping_failure_destroys_partial_address_space();
    test_rejects_entry_outside_executable_segment();
    puts("ELF user-image loader: byte copy, BSS, stack, W^X and cleanup tests passed");
    return 0;
}
