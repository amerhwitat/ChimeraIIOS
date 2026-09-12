#pragma once
#include <cstdint>
#include <string>

namespace chimera::application_net {
enum class Mode { Offline, Client, Server, Host, P2P, Hybrid };
struct Profile { std::string nickname{"Player"}; std::string avatar_ref; };
struct Config { Mode mode{Mode::Offline}; std::string bind_host{"127.0.0.1"}; std::uint16_t port{45678}; std::string endpoint; std::string room{"main"}; Profile profile{}; bool enable_p2p{true}; bool tls{true}; };

class Controller {
public:
  virtual ~Controller() = default;
  virtual bool start(const Config&) = 0;
  virtual void stop() = 0;
};
}
