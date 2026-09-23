#pragma once
#include <atomic>
#include <condition_variable>
#include <cstddef>
#include <functional>
#include <memory>
#include <mutex>
#include <queue>
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
 struct State { std::mutex m; std::condition_variable cv; std::queue<std::function<void(std::size_t)>> q; };
 std::shared_ptr<State> state_;
 std::vector<std::thread> workers_;
 std::atomic<bool> stopping_{false};
};
}