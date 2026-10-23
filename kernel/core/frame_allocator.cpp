#include <stdint.h>
#include <stddef.h>
#if defined(_MSC_VER)
#include <intrin.h>
#endif
#include "chimera/frame_allocator.h"
#include "chimera/multiboot_modules.h"


namespace {
constexpr uint32_t PAGE_COUNT = static_cast<uint32_t>(KORONOS_FRAME_PHYS_LIMIT / KORONOS_FRAME_SIZE);
constexpr uint32_t WORD_BITS = 32u;
constexpr uint32_t BITMAP_WORDS = PAGE_COUNT / WORD_BITS;
constexpr uint32_t FIRST_ALLOCATABLE_PAGE = 0x100000u / static_cast<uint32_t>(KORONOS_FRAME_SIZE);
uint32_t free_bitmap[BITMAP_WORDS];
uint32_t allocated_bitmap[BITMAP_WORDS];
volatile uint32_t allocator_lock = 0;
bool initialized = false;
uint64_t free_pages = 0;
uint16_t vm_frame_refs[PAGE_COUNT]{};
volatile uint32_t vm_ref_lock = 0;
static void vm_lock() { while (__sync_lock_test_and_set(&vm_ref_lock, 1u)) {} }
static void vm_unlock() { __sync_lock_release(&vm_ref_lock); }
static bool vm_frame_index(uint64_t address, uint32_t *index) {
    if (!index || (address & (KORONOS_FRAME_SIZE - 1u)) != 0u || address >= KORONOS_FRAME_PHYS_LIMIT) return false;
    *index = static_cast<uint32_t>(address / KORONOS_FRAME_SIZE);
    return *index >= FIRST_ALLOCATABLE_PAGE && *index < PAGE_COUNT;
}

struct Mb2Tag { uint32_t type, size; };
struct Mb2MmapTag { uint32_t type, size, entry_size, entry_version; };
struct Mb2MmapEntry { uint64_t address, length; uint32_t type, reserved; };

static void lock() {
#if defined(_MSC_VER)
    // MSVC host tests use the platform interlocked primitive; the freestanding
    // GCC/Clang kernel keeps its compiler intrinsic and needs no hosted runtime.
    while (_InterlockedExchange(reinterpret_cast<volatile long *>(&allocator_lock), 1) != 0) {}
#else
    while (__sync_lock_test_and_set(&allocator_lock, 1u)) {}
#endif
}
static void unlock() {
#if defined(_MSC_VER)
    (void)_InterlockedExchange(reinterpret_cast<volatile long *>(&allocator_lock), 0);
#else
    __sync_lock_release(&allocator_lock);
#endif
}
static bool bit(const uint32_t *map, uint32_t index) {
    return (map[index / WORD_BITS] & (1u << (index % WORD_BITS))) != 0;
}
static void set_bit(uint32_t *map, uint32_t index) {
    map[index / WORD_BITS] |= (1u << (index % WORD_BITS));
}
static void clear_bit(uint32_t *map, uint32_t index) {
    map[index / WORD_BITS] &= ~(1u << (index % WORD_BITS));
}
static uint64_t min_u64(uint64_t a, uint64_t b) { return a < b ? a : b; }

static void add_usable_range(uint64_t start, uint64_t length) {
    if (!length || start >= KORONOS_FRAME_PHYS_LIMIT || start > UINT64_MAX - length) return;
    uint64_t end = min_u64(start + length, KORONOS_FRAME_PHYS_LIMIT);
    uint64_t first = (start + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
    uint64_t last = end / KORONOS_FRAME_SIZE;
    if (first < FIRST_ALLOCATABLE_PAGE) first = FIRST_ALLOCATABLE_PAGE;
    if (last > PAGE_COUNT) last = PAGE_COUNT;
    for (uint64_t p = first; p < last; ++p) {
        uint32_t index = static_cast<uint32_t>(p);
        if (!bit(free_bitmap, index) && !bit(allocated_bitmap, index)) {
            set_bit(free_bitmap, index);
            ++free_pages;
        }
    }
}
static void reserve_range(uint64_t start, uint64_t length) {
    if (!length || start >= KORONOS_FRAME_PHYS_LIMIT || start > UINT64_MAX - length) return;
    uint64_t end = min_u64(start + length, KORONOS_FRAME_PHYS_LIMIT);
    uint64_t first = start / KORONOS_FRAME_SIZE;
    uint64_t last = (end + KORONOS_FRAME_SIZE - 1u) / KORONOS_FRAME_SIZE;
    if (last > PAGE_COUNT) last = PAGE_COUNT;
    for (uint64_t p = first; p < last; ++p) {
        uint32_t index = static_cast<uint32_t>(p);
        if (bit(free_bitmap, index)) {
            clear_bit(free_bitmap, index);
            --free_pages;
        }
        clear_bit(allocated_bitmap, index);
    }
}
static bool parse_mmap(uint64_t info) {
    if (!info) return false;
    const uint8_t *base = reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(info));
    const uint32_t total = *reinterpret_cast<const uint32_t *>(base);
    if (total < 16u || total > 16u * 1024u * 1024u) return false;
    bool found = false;
    for (uint32_t off = 8u; off <= total - 8u;) {
        const Mb2Tag *tag = reinterpret_cast<const Mb2Tag *>(base + off);
        if (tag->size < 8u || tag->size > total - off) return false;
        if (tag->type == 0u) break;
        if (tag->type == 6u) {
            if (tag->size < sizeof(Mb2MmapTag)) return false;
            const Mb2MmapTag *mmap = reinterpret_cast<const Mb2MmapTag *>(tag);
            if (mmap->entry_size < sizeof(Mb2MmapEntry)) return false;
            const uint32_t bytes = tag->size - sizeof(Mb2MmapTag);
            if (bytes % mmap->entry_size != 0u) return false;
            for (uint32_t pos = sizeof(Mb2MmapTag); pos < tag->size; pos += mmap->entry_size) {
                const Mb2MmapEntry *entry = reinterpret_cast<const Mb2MmapEntry *>(base + off + pos);
                if (entry->type == 1u) add_usable_range(entry->address, entry->length);
            }
            found = true;
            break;
        }
        const uint64_t next = (static_cast<uint64_t>(off) + tag->size + 7u) & ~7ull;
        if (next <= off || next > total) return false;
        off = static_cast<uint32_t>(next);
    }
    return found;
}
}

extern "C" int koronos_frame_allocator_init(uint64_t info, uint64_t kernel_base, uint64_t kernel_end) {
    for (uint32_t i = 0; i < BITMAP_WORDS; ++i) {
        free_bitmap[i] = 0;
        allocated_bitmap[i] = 0;
    }
    free_pages = 0;
    initialized = false;
    for (uint32_t i = 0; i < PAGE_COUNT; ++i) vm_frame_refs[i] = 0;
    vm_ref_lock = 0;
    if (!parse_mmap(info)) return -1;

    const uint8_t *base = reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(info));
    const uint32_t total = *reinterpret_cast<const uint32_t *>(base);
    reserve_range(0, 0x100000u);
    if (kernel_base < 0x100000u || kernel_end <= kernel_base || kernel_end > KORONOS_FRAME_PHYS_LIMIT) return -3;
    reserve_range(kernel_base, kernel_end - kernel_base);
    reserve_range(info, total);
    for (uint32_t i = 0; i < chimera_multiboot_module_count(); ++i) {
        const chimera_boot_module *module = chimera_multiboot_module(i);
        if (module) reserve_range(module->base, module->size);
    }
    initialized = free_pages != 0;
    return initialized ? 0 : -2;
}

extern "C" uint64_t koronos_frame_alloc_contiguous(uint32_t count) {
    if (!initialized || count == 0 || count > PAGE_COUNT - FIRST_ALLOCATABLE_PAGE) return 0;
    lock();
    uint32_t run = 0;
    uint32_t first = FIRST_ALLOCATABLE_PAGE;
    for (uint32_t i = FIRST_ALLOCATABLE_PAGE; i < PAGE_COUNT; ++i) {
        if (bit(free_bitmap, i)) {
            if (run == 0) first = i;
            if (++run == count) {
                for (uint32_t p = first; p < first + count; ++p) {
                    clear_bit(free_bitmap, p);
                    set_bit(allocated_bitmap, p);
                }
                free_pages -= count;
                unlock();
                return static_cast<uint64_t>(first) * KORONOS_FRAME_SIZE;
            }
        } else {
            run = 0;
        }
    }
    unlock();
    return 0;
}
extern "C" uint64_t koronos_frame_alloc(void) {
    return koronos_frame_alloc_contiguous(1);
}
extern "C" int koronos_frame_free_contiguous(uint64_t address, uint32_t count) {
    if (!initialized || count == 0 || (address & (KORONOS_FRAME_SIZE - 1u)) != 0u ||
        address >= KORONOS_FRAME_PHYS_LIMIT || count > PAGE_COUNT) return -1;
    const uint64_t first64 = address / KORONOS_FRAME_SIZE;
    if (first64 < FIRST_ALLOCATABLE_PAGE || first64 + count > PAGE_COUNT) return -1;
    const uint32_t first = static_cast<uint32_t>(first64);
    lock();
    for (uint32_t p = first; p < first + count; ++p) {
        if (!bit(allocated_bitmap, p) || bit(free_bitmap, p)) {
            unlock();
            return -2;
        }
    }
    for (uint32_t p = first; p < first + count; ++p) {
        clear_bit(allocated_bitmap, p);
        set_bit(free_bitmap, p);
    }
    free_pages += count;
    unlock();
    return 0;
}
extern "C" int koronos_frame_free(uint64_t address) {
    return koronos_frame_free_contiguous(address, 1);
}
extern "C" uint64_t koronos_frame_free_count(void) {
    if (!initialized) return 0;
    lock();
    const uint64_t result = free_pages;
    unlock();
    return result;
}

extern "C" uint64_t koronos_vm_frame_alloc_contiguous(uint32_t count) {
    const uint64_t base = koronos_frame_alloc_contiguous(count);
    if (!base) return 0;
    const uint32_t first = static_cast<uint32_t>(base / KORONOS_FRAME_SIZE);
    vm_lock();
    for (uint32_t i = 0; i < count; ++i) {
        if (vm_frame_refs[first + i] != 0u) { vm_unlock(); (void)koronos_frame_free_contiguous(base, count); return 0; }
    }
    for (uint32_t i = 0; i < count; ++i) vm_frame_refs[first + i] = 1u;
    vm_unlock();
    return base;
}
extern "C" uint64_t koronos_vm_frame_alloc(void) { return koronos_vm_frame_alloc_contiguous(1u); }
extern "C" int koronos_vm_frame_retain(uint64_t address) {
    uint32_t index = 0;
    if (!vm_frame_index(address, &index)) return -1;
    vm_lock();
    if (vm_frame_refs[index] == 0u || vm_frame_refs[index] == UINT16_MAX) { vm_unlock(); return -2; }
    ++vm_frame_refs[index]; vm_unlock(); return 0;
}
extern "C" int koronos_vm_frame_release(uint64_t address) {
    uint32_t index = 0;
    if (!vm_frame_index(address, &index)) return -1;
    vm_lock();
    if (vm_frame_refs[index] == 0u) { vm_unlock(); return -2; }
    --vm_frame_refs[index]; const bool reclaim = vm_frame_refs[index] == 0u; vm_unlock();
    if (!reclaim || koronos_frame_free(address) == 0) return 0;
    vm_lock(); if (vm_frame_refs[index] == 0u) vm_frame_refs[index] = 1u; vm_unlock(); return -3;
}
extern "C" int koronos_vm_frame_release_contiguous(uint64_t address, uint32_t count) {
    if (!count || (address & (KORONOS_FRAME_SIZE - 1u)) != 0u || address >= KORONOS_FRAME_PHYS_LIMIT ||
        static_cast<uint64_t>(count) > (KORONOS_FRAME_PHYS_LIMIT - address) / KORONOS_FRAME_SIZE) return -1;
    const uint32_t first = static_cast<uint32_t>(address / KORONOS_FRAME_SIZE);
    vm_lock();
    for (uint32_t i = 0; i < count; ++i) { if (first + i < FIRST_ALLOCATABLE_PAGE || vm_frame_refs[first + i] == 0u) { vm_unlock(); return -2; } }
    for (uint32_t i = 0; i < count; ++i) --vm_frame_refs[first + i];
    vm_unlock();
    int result = 0;
    for (uint32_t i = 0; i < count; ++i) {
        vm_lock(); const bool reclaim = vm_frame_refs[first + i] == 0u; vm_unlock();
        if (reclaim && koronos_frame_free(address + static_cast<uint64_t>(i) * KORONOS_FRAME_SIZE) != 0) result = -3;
    }
    return result;
}
extern "C" uint32_t koronos_vm_frame_refcount(uint64_t address) {
    uint32_t index = 0; if (!vm_frame_index(address, &index)) return 0;
    vm_lock(); const uint32_t refs = vm_frame_refs[index]; vm_unlock(); return refs;
}
