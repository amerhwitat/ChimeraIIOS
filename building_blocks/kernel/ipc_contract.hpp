#pragma once
#include <cstdint>

namespace chimera::kernel {

enum class CapabilityType : std::uint8_t { Memory, Ipc, Device, Network, Service };
enum Rights : std::uint32_t { None = 0, Read = 1, Write = 2, Execute = 4, Grant = 8 };

struct Capability {
    std::uint64_t object{};
    CapabilityType type{CapabilityType::Ipc};
    std::uint32_t rights{};
    std::uint32_t generation{};

    constexpr bool valid() const noexcept { return object != 0 && generation != 0; }
    constexpr bool allows(std::uint32_t r) const noexcept { return (rights & r) == r; }
};

struct IpcMessage {
    std::uint64_t sender{};
    std::uint64_t endpoint{};
    std::uint32_t length{};
    std::uint32_t flags{};
};

} // namespace chimera::kernel
