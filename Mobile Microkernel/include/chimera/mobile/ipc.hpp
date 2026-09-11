#pragma once
#include <cstddef>
#include <cstdint>

namespace chimera::mobile {

using CapabilityId = std::uint64_t;
using EndpointId = std::uint64_t;

struct MessageHeader {
    EndpointId sender{};
    EndpointId receiver{};
    CapabilityId capability{};
    std::uint32_t length{};
    std::uint32_t sequence{};
};

class IpcEndpoint {
public:
    explicit IpcEndpoint(EndpointId id) : id_(id) {}
    EndpointId id() const noexcept { return id_; }
    bool authorize(CapabilityId capability) const noexcept { return capability != 0; }

private:
    EndpointId id_{};
};

} // namespace chimera::mobile
