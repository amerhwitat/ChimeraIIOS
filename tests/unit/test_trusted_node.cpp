#include "chimera/neural_node.hpp"
#include <cassert>

int main() {
    chimera::neural::TrustedNodeProtocol protocol;
    chimera::neural::NodeAdvertisement peer;
    peer.protocol = "chimera-node/1";
    peer.capabilities = 1;
    chimera::neural::KnowledgeEnvelope envelope;
    envelope.sequence = 1;
    envelope.signed_payload = true;
    auto accepted = protocol.validate(peer, envelope);
    assert(accepted.accepted);
    envelope.signed_payload = false;
    auto rejected = protocol.validate(peer, envelope);
    assert(!rejected.accepted);
    return 0;
}
