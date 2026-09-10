#pragma once

#include <bit>
#include <cstdint>
#include <string_view>
#include "chimera/RegisterN.hpp"
#include "chimera/isa_extension_catalog.hpp"

namespace chimera::isa {

inline unsigned clz64(std::uint64_t x) noexcept { return x ? std::countl_zero(x) : 64; }
inline unsigned ctz64(std::uint64_t x) noexcept { return x ? std::countr_zero(x) : 64; }
inline unsigned popcnt64(std::uint64_t x) noexcept { return std::popcount(x); }

inline Register8192 vector_add(const Register8192 &a, const Register8192 &b) noexcept {
    return a + b;
}

inline Register8192 vector_madd(const Register8192 &a, const Register8192 &b,
                                const Register8192 &acc) noexcept {
    Register8192 out = acc;
    for (std::size_t i = 0; i < Register8192::kLanes; ++i)
        out.set_u64(i, out.lane(i) + a.lane(i) * b.lane(i));
    return out;
}

inline std::uint32_t crc32(std::uint32_t crc, std::uint64_t value) noexcept {
    // CRC-32C polynomial, suitable as the portable semantic definition for
    // the Chimera CRC32 extension. Hardware-specific lowering is separate.
    constexpr std::uint32_t poly = 0x82F63B78u;
    for (unsigned byte = 0; byte < 8; ++byte) {
        crc ^= static_cast<std::uint32_t>(value & 0xffu);
        value >>= 8;
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) ? poly : 0u);
    }
    return crc;
}

inline bool has_extension(std::string_view name) noexcept {
    return extension_catalog.contains(name);
}

} // namespace chimera::isa
