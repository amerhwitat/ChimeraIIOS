#pragma once
#include <cstdint>

namespace chimera::hive {

enum class ValueType : std::uint8_t { Boolean, Integer, String, Bytes };

struct Entry {
    std::uint64_t key_hash{};
    ValueType type{ValueType::Bytes};
    std::uint32_t length{};
    std::uint32_t generation{};
    std::uint32_t permissions{};
};

constexpr bool valid(const Entry& e) noexcept {
    return e.key_hash != 0 && e.generation != 0;
}

} // namespace chimera::hive
