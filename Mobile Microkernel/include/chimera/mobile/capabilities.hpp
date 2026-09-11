#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class CapabilityType : std::uint8_t {
    Ipc, Memory, Interrupt, Device, Power, Debug
};

struct Capability {
    std::uint64_t object_id{};
    CapabilityType type{CapabilityType::Ipc};
    std::uint32_t rights{};
    std::uint64_t generation{};

    bool valid() const noexcept { return object_id != 0 && generation != 0; }
};

enum Rights : std::uint32_t {
    Read = 1u << 0,
    Write = 1u << 1,
    Execute = 1u << 2,
    Grant = 1u << 3
};

} // namespace chimera::mobile
