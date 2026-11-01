#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "chimera/frame_allocator.h"
#include "chimera/multiboot_modules.h"
extern "C" uint32_t chimera_multiboot_module_count(void) { return 0; }
extern "C" const chimera_boot_module *chimera_multiboot_module(uint32_t) { return nullptr; }
#pragma pack(push, 1)
struct Tag { uint32_t type, size; };
struct MmapTag { uint32_t type, size, entry_size, entry_version; };
struct MmapEntry { uint64_t address, length; uint32_t type, reserved; };
#pragma pack(pop)
int main() {
    alignas(8) uint8_t info[56]{};
    const uint32_t total = sizeof(info);
    memcpy(info, &total, sizeof(total));
    MmapTag mmap{6u, 40u, 24u, 0u};
    memcpy(info + 8u, &mmap, sizeof(mmap));
    MmapEntry high{0x100000000ull, 0x800000ull, 1u, 0u};
    memcpy(info + 24u, &high, sizeof(high));
    Tag end{0u, 8u};
    memcpy(info + 48u, &end, sizeof(end));
    if (koronos_frame_allocator_init(reinterpret_cast<uint64_t>(info), 0x100000ull, 0x200000ull) != 0) return 1;
    const uint64_t first = koronos_frame_alloc();
    if (first <= 0xFFFFFFFFull || first != 0x100000000ull) return 2;
    const uint64_t run = koronos_frame_alloc_contiguous(2u);
    if (run <= 0xFFFFFFFFull || koronos_frame_free_contiguous(run, 2u) != 0) return 3;
    if (koronos_frame_free(first) != 0) return 4;
    puts("Koronos high-memory frame allocator test passed (>4 GiB)");
    return 0;
}
