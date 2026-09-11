#pragma once
#include <cstdint>

namespace chimera::boot {

inline constexpr std::uint32_t kBootInfoVersion = 3;

enum BootFlags : std::uint32_t {
    BIOS = 1u << 0,
    UEFI = 1u << 1,
    SECURE_BOOT = 1u << 2,
    DUAL_BOOT = 1u << 3,
    DEVICE_TREE = 1u << 4,
    ACPI = 1u << 5,
};

struct BootInfo {
    std::uint32_t version{kBootInfoVersion};
    std::uint32_t size{sizeof(BootInfo)};
    std::uint64_t memory_bytes{};
    std::uint64_t kernel_physical_base{};
    std::uint64_t kernel_size{};
    std::uint64_t firmware_table{};
    std::uint32_t flags{};
    std::uint32_t cpu_count{};
};

constexpr bool valid(const BootInfo& b) noexcept {
    return b.version == kBootInfoVersion &&
           b.size >= sizeof(BootInfo) &&
           b.memory_bytes != 0 && b.cpu_count != 0;
}

} // namespace chimera::boot
