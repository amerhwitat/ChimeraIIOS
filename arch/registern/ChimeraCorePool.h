#pragma once
#include <atomic>
#include <cstddef>
#include <functional>
#include <thread>
#include <vector>

namespace chimera::arch {
struct CoreTopology { std::size_t physical_cores{}, logical_threads{}; bool smt{}; };
CoreTopology detect_host_topology();

class ChimeraCorePool {
public:
    explicit ChimeraCorePool(std::size_t logical_cores=0);
    ~ChimeraCorePool();
    ChimeraCorePool(const ChimeraCorePool&)=delete;
    void submit(std::function<void(std::size_t)> job);
    void stop();
    std::size_t size() const noexcept { return workers_.size(); }
private:
    std::vector<std::thread> workers_;
    std::atomic<bool> stopping_{false};
};
}
