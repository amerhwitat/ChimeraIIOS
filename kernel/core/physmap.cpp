#include <stdint.h>
#include "chimera/physmap.h"

namespace {
constexpr uint64_t PRESENT = 1ull;
constexpr uint64_t WRITABLE = 2ull;
constexpr uint64_t USER = 4ull;
constexpr uint64_t LARGE = 0x80ull;
constexpr uint64_t TABLE_ADDRESS_MASK = 0x000FFFFFFFFFF000ull;
constexpr uint64_t LARGE_ADDRESS_MASK = 0x000FFFFFFFE00000ull;
constexpr uint64_t LARGE_PAGE_SIZE = 0x200000ull;
constexpr uint32_t LARGE_PAGE_COUNT = 2048u;
volatile uint32_t map_ready;

static bool table_address(uint64_t entry, uint64_t *address) {
    if (!(entry & PRESENT) || !(entry & WRITABLE) || (entry & USER) || (entry & LARGE))
        return false;
    *address = entry & TABLE_ADDRESS_MASK;
    return *address != 0 && *address < KORONOS_PHYSMAP_LIMIT;
}

static bool validate_boot_tables(uint64_t root_physical) {
    if (!root_physical || root_physical >= KORONOS_PHYSMAP_LIMIT ||
        (root_physical & 0xFFFu)) return false;
    const auto *root = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(root_physical));
    uint64_t pdpt_physical = 0;
    if (!table_address(root[0], &pdpt_physical)) return false;
    for (uint32_t i = 1; i < 512u; ++i) if (root[i] & PRESENT) return false;

    const auto *pdpt = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(pdpt_physical));
    uint64_t first_pd_physical = 0;
    for (uint32_t pdpt_index = 0; pdpt_index < 4u; ++pdpt_index) {
        uint64_t pd_physical = 0;
        if (!table_address(pdpt[pdpt_index], &pd_physical)) return false;
        if (pdpt_index == 0) first_pd_physical = pd_physical;
        else if (pd_physical != first_pd_physical + static_cast<uint64_t>(pdpt_index) * 4096u)
            return false;
        const auto *pd = reinterpret_cast<const uint64_t *>(static_cast<uintptr_t>(pd_physical));
        for (uint32_t pd_index = 0; pd_index < 512u; ++pd_index) {
            const uint32_t global_index = pdpt_index * 512u + pd_index;
            const uint64_t entry = pd[pd_index];
            if ((entry & (PRESENT | WRITABLE | LARGE)) != (PRESENT | WRITABLE | LARGE) ||
                (entry & USER) ||
                (entry & LARGE_ADDRESS_MASK) != static_cast<uint64_t>(global_index) * LARGE_PAGE_SIZE)
                return false;
        }
    }
    for (uint32_t i = 4u; i < 512u; ++i) if (pdpt[i] & PRESENT) return false;
    return true;
}
}

extern "C" int koronos_physmap_validate_range(uint64_t physical, uint64_t length) {
    if (!length || physical >= KORONOS_PHYSMAP_LIMIT ||
        length > KORONOS_PHYSMAP_LIMIT - physical) return -1;
    return 0;
}

extern "C" int koronos_physmap_init(void) {
    if (map_ready) return -1;
#if defined(__x86_64__)
    uint64_t cr3 = 0;
    __asm__ volatile("mov %%cr3, %0" : "=r"(cr3));
    const uint64_t root = cr3 & TABLE_ADDRESS_MASK;
    if (!validate_boot_tables(root)) return -2;
    __sync_synchronize();
    map_ready = 1;
    return 0;
#else
    return -3;
#endif
}

extern "C" void *koronos_phys_to_virt(uint64_t physical, uint64_t length) {
    if (!map_ready || koronos_physmap_validate_range(physical, length) != 0) return nullptr;
    return reinterpret_cast<void *>(static_cast<uintptr_t>(physical));
}

extern "C" int koronos_physmap_ready(void) { return map_ready ? 1 : 0; }
