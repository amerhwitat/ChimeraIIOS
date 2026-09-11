#pragma once
#include <cstddef>
#include <cstdint>

namespace chimera::memory {

struct PageRange {
    std::uintptr_t base{};
    std::size_t pages{};
    constexpr std::uintptr_t end() const noexcept { return base + pages * 4096u; }
};

struct DmaDescriptor {
    std::uintptr_t physical{};
    std::uint32_t length{};
    std::uint16_t flags{};
    std::uint16_t queue{};
};

enum DmaFlags : std::uint16_t { Read = 1, Write = 2, Interrupt = 4 };

constexpr bool valid(const DmaDescriptor& d) noexcept {
    return d.physical != 0 && d.length != 0 && (d.flags & (Read | Write)) != 0;
}

} // namespace chimera::memory
