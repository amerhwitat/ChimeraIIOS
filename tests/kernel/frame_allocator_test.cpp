#include <cassert>
#include <cstdint>
#include <cstring>
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
    alignas(8) uint8_t info[64]{};
    const uint32_t total = 56;
    std::memcpy(info, &total, sizeof(total));
    MmapTag mmap{6, 40, 24, 0};
    std::memcpy(info + 8, &mmap, sizeof(mmap));
    MmapEntry usable{0x100000, 63ull * 1024ull * 1024ull, 1, 0};
    std::memcpy(info + 24, &usable, sizeof(usable));
    Tag end{0, 8};
    std::memcpy(info + 48, &end, sizeof(end));

    assert(koronos_frame_allocator_init(reinterpret_cast<uintptr_t>(info), 0x100000, 0x200000) == 0);
    assert(koronos_frame_free_count() == 15872);
    const uint64_t first = koronos_frame_alloc_contiguous(3);
    assert(first >= 0x200000 && (first & 4095u) == 0);
    assert(koronos_frame_free_count() == 15869);
    assert(koronos_frame_free_contiguous(first, 3) == 0);
    assert(koronos_frame_free_count() == 15872);
    assert(koronos_frame_free_contiguous(first, 3) != 0);
    assert(koronos_frame_alloc() != 0);
    assert(koronos_frame_allocator_init(reinterpret_cast<uintptr_t>(info), 0x100000, 0x200000) == 0);
    assert(koronos_frame_free_count() == 15872);
    return 0;
}
