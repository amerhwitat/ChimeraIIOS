#pragma once

#include <string>
#include <vector>

namespace chimera::bizx {

struct PeerRecord {
    std::string peer_id;          // pseudonymous application identifier
    std::string display_name;
    std::string last_seen_utc;
    std::string network_hint;     // relay-or-direct; never a raw IP address
    std::vector<std::string> capabilities;
};

// Application discovery is opt-in. This contract intentionally does not
// persist raw player IP addresses or scan arbitrary Internet hosts.
struct PeerDirectoryPolicy {
    bool opt_in_required = true;
    bool persist_raw_ip = false;
    bool public_internet_scanning = false;
};

} // namespace chimera::bizx
