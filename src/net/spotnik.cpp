#include "chimera/spotnik.hpp"
#include <queue>
#include <mutex>
namespace chimera {
class LoopbackSpotnik final : public Spotnik {
    std::queue<NetFrame> q_; std::mutex m_;
public:
    bool send_zc(const NetFrame& f) override { std::lock_guard<std::mutex> g(m_); q_.push(f); return true; }
    bool recv_zc(NetFrame& f) override { std::lock_guard<std::mutex> g(m_); if(q_.empty()) return false; f=q_.front(); q_.pop(); return true; }
    void release_rx(const NetFrame&) override {}
};
}
