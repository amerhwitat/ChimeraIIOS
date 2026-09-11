#pragma once
#include <cstddef>
#include <cstdint>

namespace chimera::spotnik {

struct Packet {
    std::uint64_t buffer_id{};
    std::uint32_t length{};
    std::uint16_t queue{};
    std::uint16_t flags{};
};

struct QueueContract {
    Packet* entries{};
    std::size_t capacity{};
    std::size_t producer{};
    std::size_t consumer{};

    constexpr bool valid() const noexcept {
        return entries != nullptr && capacity != 0 && producer < capacity && consumer < capacity;
    }
    constexpr bool empty() const noexcept { return producer == consumer; }
};

} // namespace chimera::spotnik
