#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace chimera::neural {

struct NodeId { std::array<std::uint8_t, 32> value{}; };
struct Digest { std::array<std::uint8_t, 32> value{}; };

struct TrustPolicy {
    bool require_mutual_authentication{true};
    bool require_signed_capabilities{true};
    bool require_fresh_nonce{true};
    bool allow_tofu{false};
    std::uint64_t max_clock_skew_ms{30000};
};

struct NodeAdvertisement {
    NodeId node_id{};
    std::string endpoint;
    std::string protocol{"chimera-node/1"};
    std::string architecture;
    std::uint64_t capabilities{0};
    Digest identity_key_digest{};
    std::uint64_t expires_at_ms{0};
};

struct KnowledgeEnvelope {
    NodeId origin{};
    std::uint64_t sequence{0};
    Digest content_digest{};
    std::vector<std::uint8_t> payload;
    bool signed_payload{false};
};

struct SyncDecision {
    bool accepted{false};
    bool requires_reauthentication{false};
    std::string reason;
};

// Transport-neutral contract. Implementations must use an authenticated,
// encrypted channel and MUST NOT perform unsolicited Internet port scanning.
class TrustedNodeProtocol {
public:
    explicit TrustedNodeProtocol(TrustPolicy policy = {}) : policy_(policy) {}

    SyncDecision validate(const NodeAdvertisement& peer,
                          const KnowledgeEnvelope& envelope) const;

    const TrustPolicy& policy() const noexcept { return policy_; }

private:
    TrustPolicy policy_;
};

} // namespace chimera::neural
