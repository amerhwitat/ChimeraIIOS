#pragma once
#include <cstdint>
namespace chimera {
struct BootInfo { uint64_t magic, version, size, crc32; uint64_t memory_map, memory_map_count; uint64_t framebuffer, framebuffer_size; uint64_t initrd, initrd_size; uint64_t cmdline; uint64_t boot_tsc; };
constexpr uint64_t BOOTINFO_MAGIC=0x43484D32424F4F54ULL; // CHM2BOOT
}
