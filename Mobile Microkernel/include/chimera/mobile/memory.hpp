#pragma once
#include <cstddef>
#include <cstdint>

namespace chimera::mobile {

struct MemoryRegion {
    std::uint64_t base{};
    std::uint64_t size{};
    std::uint32_t attributes{};
};

enum MemoryAttributes : std::uint32_t {
    Usable = 1u << 0,
    Reserved = 1u << 1,
    Device = 1u << 2,
    Reclaimable = 1u << 3,
    Dma = 1u << 4
};

class AddressSpace {
public:
    bool map(std::uint64_t virtual_address, std::uint64_t physical_address,
             std::size_t length, std::uint32_t attributes) noexcept {
        return virtual_address != 0 && physical_address != 0 && length != 0 && attributes != 0;
    }
};

} // namespace chimera::mobile
