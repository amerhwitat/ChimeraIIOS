#include "chimera/network/ai_network.h"
#include <cassert>
int main() {
    using namespace chimera::network;
    auto p = plan_for("edge", true, true);
    assert(p.transport == Transport::WebTransport);
    assert(p.protocol == AgentProtocol::Mcp);
    assert(p.datagrams);
    assert(capability_allowed({"read_web", "browser", false}));
    assert(!capability_allowed({"write_network", "router", true}));
    return 0;
}
