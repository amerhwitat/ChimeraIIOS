#pragma once
#include <string>
#include <vector>
namespace chimera::network {
enum class Transport { Http3Quic, WebTransport, WebSocket, WasiHttp };
enum class AgentProtocol { Mcp, A2A, WebMcp };
struct Capability { std::string name; std::string resource; bool mutating{false}; };
struct NetworkPlan { Transport transport{Transport::Http3Quic}; AgentProtocol protocol{AgentProtocol::Mcp}; bool streaming{true}; bool datagrams{false}; std::vector<Capability> capabilities; };
NetworkPlan plan_for(const std::string& edition, bool low_latency, bool agent_tools);
bool capability_allowed(const Capability& capability);
} // namespace chimera::network
