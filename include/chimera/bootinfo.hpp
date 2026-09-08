#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace chimera::boot {
inline constexpr std::uint64_t kBootMagic = 0x43484D32424F4F54ULL;
inline constexpr std::uint16_t kBootVersion = 2;
inline constexpr std::size_t kMaxMemoryMapEntries = 128;

enum class MemoryType : std::uint32_t { Reserved=0, Usable=1, AcpiReclaimable=2, AcpiNvs=3, Mmio=4, Bootloader=5, Kernel=6, Initrd=7 };
struct MemoryMapEntry { std::uint64_t base{}; std::uint64_t length{}; MemoryType type{MemoryType::Reserved}; std::uint32_t attributes{}; };
struct FramebufferInfo { std::uint64_t address{}; std::uint32_t width{}; std::uint32_t height{}; std::uint32_t pitch{}; std::uint32_t format{}; };
struct BootInfo {
    std::uint64_t magic{}; std::uint16_t version{}; std::uint16_t flags{}; std::uint32_t size{}; std::uint32_t crc32{}; std::uint32_t memory_map_count{};
    std::array<MemoryMapEntry,kMaxMemoryMapEntries> memory_map{};
    FramebufferInfo framebuffer{}; std::uint64_t initrd_address{}; std::uint64_t initrd_size{}; std::uint64_t cmdline_address{}; std::uint64_t cmdline_size{};
    std::array<std::uint8_t,32> measured_boot_digest{}; std::uint64_t boot_timestamp{};
    void finalize_crc() noexcept; [[nodiscard]] bool valid() const noexcept;
};
[[nodiscard]] std::uint32_t crc32(const void*,std::size_t) noexcept;
} // namespace chimera::boot
