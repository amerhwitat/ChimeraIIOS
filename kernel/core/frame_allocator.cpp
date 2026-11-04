#include <stdint.h>
#include <stddef.h>
#include "chimera/frame_allocator.h"
#include "chimera/multiboot_modules.h"

namespace {
constexpr uint32_t PAGE_COUNT = static_cast<uint32_t>(KORONOS_FRAME_PHYS_LIMIT / KORONOS_FRAME_SIZE);
constexpr uint32_t WORD_BITS = 32u;
constexpr uint32_t BITMAP_WORDS = PAGE_COUNT / WORD_BITS;
constexpr uint32_t FIRST_ALLOCATABLE_PAGE = 0x100000u / static_cast<uint32_t>(KORONOS_FRAME_SIZE);
constexpr uint32_t MB2_TAG_END = 0u;
constexpr uint32_t MB2_TAG_MMAP = 6u;
constexpr uint32_t MB2_TAG_FRAMEBUFFER = 8u;
uint32_t free_bitmap[BITMAP_WORDS];
uint32_t allocated_bitmap[BITMAP_WORDS];
volatile uint32_t allocator_lock;
bool initialized;
uint64_t free_pages;

struct Tag { uint32_t type, size; };
struct MmapTag { uint32_t type, size, entry_size, entry_version; };
struct MmapEntry { uint64_t address, length; uint32_t type, reserved; };

static void lock() { while (__sync_lock_test_and_set(&allocator_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&allocator_lock); }
static bool bit(const uint32_t *map, uint32_t i) {
    return (map[i / WORD_BITS] & (1u << (i % WORD_BITS))) != 0;
}
static void set_bit(uint32_t *map, uint32_t i) { map[i / WORD_BITS] |= 1u << (i % WORD_BITS); }
static void clear_bit(uint32_t *map, uint32_t i) { map[i / WORD_BITS] &= ~(1u << (i % WORD_BITS)); }

static bool range_end(uint64_t start, uint64_t length, uint64_t *end) {
    if (!length || start > UINT64_MAX - length) return false;
    *end = start + length;
    return true;
}
static void reserve_range(uint64_t start, uint64_t length) {
    uint64_t end = 0;
    if (!range_end(start, length, &end) || start >= KORONOS_FRAME_PHYS_LIMIT) return;
    if (end > KORONOS_FRAME_PHYS_LIMIT) end = KORONOS_FRAME_PHYS_LIMIT;
    const uint64_t first = start / KORONOS_FRAME_SIZE;
    const uint64_t last = (end + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
    for (uint64_t p = first; p < last && p < PAGE_COUNT; ++p) {
        const uint32_t i = static_cast<uint32_t>(p);
        if (bit(free_bitmap, i)) { clear_bit(free_bitmap, i); --free_pages; }
        clear_bit(allocated_bitmap, i);
    }
}
static bool add_usable_range(uint64_t start, uint64_t length) {
    uint64_t end = 0;
    if (!range_end(start, length, &end)) return false;
    /* Explicitly reject rather than silently discard RAM the allocator cannot
       address under the current bootstrap mapping contract. */
    if (end > KORONOS_FRAME_PHYS_LIMIT) return false;
    if (start >= KORONOS_FRAME_PHYS_LIMIT) return false;
    uint64_t first = (start + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
    const uint64_t last = end / KORONOS_FRAME_SIZE;
    if (first < FIRST_ALLOCATABLE_PAGE) first = FIRST_ALLOCATABLE_PAGE;
    for (uint64_t p = first; p < last; ++p) {
        const uint32_t i = static_cast<uint32_t>(p);
        if (!bit(free_bitmap, i) && !bit(allocated_bitmap, i)) {
            set_bit(free_bitmap, i);
            ++free_pages;
        }
    }
    return true;
}
static bool parse_multiboot(uint64_t info, uint32_t *total_out) {
    if (!info || !total_out) return false;
    const uint8_t *base = reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(info));
    const uint32_t total = *reinterpret_cast<const uint32_t *>(base);
    if (total < 16u || total > 16u * 1024u * 1024u) return false;
    bool found_map = false, found_end = false;
    uint64_t framebuffer_base[8]{};
    uint64_t framebuffer_size[8]{};
    uint32_t framebuffer_count = 0;
    for (uint32_t off = 8u; off <= total - 8u;) {
        const Tag *tag = reinterpret_cast<const Tag *>(base + off);
        if (tag->size < 8u || tag->size > total - off) return false;
        if (tag->type == MB2_TAG_END) {
            if (tag->size != 8u) return false;
            found_end = true;
            break;
        }
        if (tag->type == MB2_TAG_MMAP) {
            if (found_map || tag->size < sizeof(MmapTag)) return false;
            const MmapTag *m = reinterpret_cast<const MmapTag *>(tag);
            if (m->entry_version != 0u || m->entry_size < sizeof(MmapEntry)) return false;
            const uint32_t bytes = tag->size - sizeof(MmapTag);
            if (bytes % m->entry_size) return false;
            for (uint32_t pos = sizeof(MmapTag); pos < tag->size; pos += m->entry_size) {
                const MmapEntry *entry = reinterpret_cast<const MmapEntry *>(base + off + pos);
                uint64_t end = 0;
                if (!range_end(entry->address, entry->length, &end)) return false;
                if (entry->type == 1u && !add_usable_range(entry->address, entry->length)) return false;
            }
            found_map = true;
        } else if (tag->type == MB2_TAG_FRAMEBUFFER) {
            if (tag->size < 32u) return false;
            const uint64_t address = *reinterpret_cast<const uint64_t *>(base + off + 8u);
            const uint32_t pitch = *reinterpret_cast<const uint32_t *>(base + off + 16u);
            const uint32_t height = *reinterpret_cast<const uint32_t *>(base + off + 24u);
            if (pitch && height && static_cast<uint64_t>(pitch) > UINT64_MAX / height) return false;
            const uint64_t framebuffer_bytes = static_cast<uint64_t>(pitch) * height;
            uint64_t framebuffer_end = 0;
            if (framebuffer_bytes && !range_end(address, framebuffer_bytes, &framebuffer_end)) return false;
            if (framebuffer_bytes) {
                if (framebuffer_count >= 8u) return false;
                framebuffer_base[framebuffer_count] = address;
                framebuffer_size[framebuffer_count] = framebuffer_bytes;
                ++framebuffer_count;
            }
        }
        const uint64_t next = (static_cast<uint64_t>(off) + tag->size + 7u) & ~7ull;
        if (next <= off || next > total) return false;
        off = static_cast<uint32_t>(next);
    }
    if (!found_map || !found_end) return false;
    for (uint32_t i = 0; i < framebuffer_count; ++i)
        reserve_range(framebuffer_base[i], framebuffer_size[i]);
    *total_out = total;
    return true;
}
static bool reserve_multiboot_modules(uint64_t info, uint32_t total) {
    const uint8_t *base = reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(info));
    for (uint32_t off = 8u; off <= total - 8u;) {
        const Tag *tag = reinterpret_cast<const Tag *>(base + off);
        if (tag->size < 8u || tag->size > total - off) return false;
        if (tag->type == MB2_TAG_END) return tag->size == 8u;
        if (tag->type == 3u) {
            if (tag->size < 16u) return false;
            const uint32_t module_start = *reinterpret_cast<const uint32_t *>(base + off + 8u);
            const uint32_t module_end = *reinterpret_cast<const uint32_t *>(base + off + 12u);
            if (module_end < module_start) return false;
            if (module_end > module_start)
                reserve_range(module_start, static_cast<uint64_t>(module_end - module_start));
        }
        const uint64_t next = (static_cast<uint64_t>(off) + tag->size + 7u) & ~7ull;
        if (next <= off || next > total) return false;
        off = static_cast<uint32_t>(next);
    }
    return false;
}
}

extern "C" int koronos_frame_allocator_init(uint64_t info, uint64_t kernel_base, uint64_t kernel_end) {
    if (initialized) return -1;
    for (uint32_t i = 0; i < BITMAP_WORDS; ++i) {
        free_bitmap[i] = 0;
        allocated_bitmap[i] = 0;
    }
    free_pages = 0;
    allocator_lock = 0;
    uint32_t info_size = 0;
    if (!parse_multiboot(info, &info_size)) return -2;
    if (kernel_base < 0x100000u || kernel_end <= kernel_base ||
        kernel_end > KORONOS_FRAME_PHYS_LIMIT) return -3;

    reserve_range(0, 0x100000u);
    reserve_range(kernel_base, kernel_end - kernel_base);
    reserve_range(info, info_size);
    if (!reserve_multiboot_modules(info, info_size)) return -5;
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (!module || !module->size) continue;
        reserve_range(module->base, module->size);
    }
    if (!free_pages) return -4;
    initialized = true;
    return 0;
}

extern "C" uint64_t koronos_frame_alloc_contiguous(uint32_t count) {
    if (!initialized || !count || count > PAGE_COUNT - FIRST_ALLOCATABLE_PAGE) return 0;
    lock();
    uint32_t run = 0, first = FIRST_ALLOCATABLE_PAGE;
    for (uint32_t i = FIRST_ALLOCATABLE_PAGE; i < PAGE_COUNT; ++i) {
        if (bit(free_bitmap, i)) {
            if (!run) first = i;
            if (++run == count) {
                for (uint32_t p = first; p < first + count; ++p) {
                    clear_bit(free_bitmap, p); set_bit(allocated_bitmap, p);
                }
                free_pages -= count;
                unlock();
                return static_cast<uint64_t>(first) * KORONOS_FRAME_SIZE;
            }
        } else run = 0;
    }
    unlock();
    return 0;
}
extern "C" uint64_t koronos_frame_alloc(void) { return koronos_frame_alloc_contiguous(1); }
extern "C" int koronos_frame_free_contiguous(uint64_t address, uint32_t count) {
    if (!initialized || !count || (address & (KORONOS_FRAME_SIZE - 1u)) ||
        address >= KORONOS_FRAME_PHYS_LIMIT || count > PAGE_COUNT) return -1;
    const uint64_t first64 = address / KORONOS_FRAME_SIZE;
    if (first64 < FIRST_ALLOCATABLE_PAGE || first64 + count > PAGE_COUNT) return -1;
    const uint32_t first = static_cast<uint32_t>(first64);
    lock();
    for (uint32_t p = first; p < first + count; ++p) {
        if (!bit(allocated_bitmap, p) || bit(free_bitmap, p)) { unlock(); return -2; }
    }
    for (uint32_t p = first; p < first + count; ++p) {
        clear_bit(allocated_bitmap, p); set_bit(free_bitmap, p);
    }
    free_pages += count;
    unlock();
    return 0;
}
extern "C" int koronos_frame_free(uint64_t address) { return koronos_frame_free_contiguous(address, 1); }
extern "C" uint64_t koronos_frame_free_count(void) {
    if (!initialized) return 0;
    lock(); const uint64_t n = free_pages; unlock(); return n;
}
extern "C" uint64_t koronos_frame_managed_limit(void) { return KORONOS_FRAME_PHYS_LIMIT; }
