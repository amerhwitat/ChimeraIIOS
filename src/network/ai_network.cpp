#include "chimera/network/ai_network.h"
namespace chimera::network {
NetworkPlan plan_for(const std::string& edition, bool low_latency, bool agent_tools) {
    NetworkPlan p;
    p.transport = low_latency ? Transport::WebTransport : Transport::Http3Quic;
    if (edition == "cvel" || edition == "mobile" || edition == "edge") p.transport = low_latency ? Transport::WebTransport : Transport::WasiHttp;
    p.protocol = agent_tools ? AgentProtocol::Mcp : AgentProtocol::A2A;
    p.streaming = true;
    p.datagrams = low_latency;
    if (agent_tools) p.capabilities.push_back({"read_web", "browser", false});
    return p;
}
bool capability_allowed(const Capability& capability) {
    if (capability.name.empty() || capability.resource.empty()) return false;
    return !capability.mutating;
}
} // namespace chimera::network
