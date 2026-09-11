#pragma once
#include <cstdint>

namespace chimera::mobile {

inline constexpr std::uint32_t MOBILE_ABI_VERSION = 1;
inline constexpr std::uint32_t BOOT_FLAG_UEFI = 1u << 0;
inline constexpr std::uint32_t BOOT_FLAG_DEVICE_TREE = 1u << 1;
inline constexpr std::uint32_t BOOT_FLAG_SECURE_BOOT = 1u << 2;
inline constexpr std::uint32_t BOOT_FLAG_VERIFIED_BOOT = 1u << 3;
inline constexpr std::uint32_t BOOT_FLAG_RISCV = 1u << 4;
inline constexpr std::uint32_t BOOT_FLAG_AARCH64 = 1u << 5;

struct AbiHeader {
    std::uint32_t version{MOBILE_ABI_VERSION};
    std::uint32_t size{sizeof(AbiHeader)};
};

} // namespace chimera::mobile
