#include "chimera/neural_node.hpp"

namespace chimera::neural {

SyncDecision TrustedNodeProtocol::validate(const NodeAdvertisement& peer,
                                           const KnowledgeEnvelope& envelope) const {
    SyncDecision result{};
    if (peer.protocol != "chimera-node/1") {
        result.reason = "unsupported node protocol";
        return result;
    }
    if (policy_.require_signed_capabilities && peer.capabilities == 0) {
        result.reason = "peer advertised no signed capabilities";
        return result;
    }
    if (policy_.require_signed_capabilities && !envelope.signed_payload) {
        result.reason = "knowledge envelope is unsigned";
        return result;
    }
    if (envelope.sequence == 0) {
        result.reason = "invalid synchronization sequence";
        return result;
    }
    result.accepted = true;
    result.reason = "authenticated protocol and signed envelope required; cryptographic verification delegated to transport/security service";
    return result;
}

} // namespace chimera::neural
