#pragma once
#include <array>
#include <cstdint>
#include <string_view>

namespace chimera::p2p {
struct EnvelopeHeader {
    std::uint32_t version{1};
    std::uint64_t sequence{0};
    std::string_view type{};
    std::string_view node_id{};
};

// Transport-neutral contract. Cryptographic hashing/authentication is provided
// by the platform crypto layer; this type keeps protocol state language-neutral.
struct PeerCapabilities {
    bool snapshots{true};
    bool deltas{true};
    bool pubsub{true};
    bool multidimensional_128d{true};
};
}
