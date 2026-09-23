#include "ChimeraCorePool.h"
#include <fstream>
#include <stdexcept>

namespace chimera::arch {

CoreTopology detect_host_topology() {
    const auto logical = std::thread::hardware_concurrency();
    CoreTopology t{logical ? logical : 1, logical ? logical : 1, false};
#if defined(__linux__)
    std::ifstream f("/sys/devices/system/cpu/smt/active");
    int active = 0;
    if (f >> active) {
        t.smt = active != 0;
    }
#endif
    return t;
}

ChimeraCorePool::ChimeraCorePool(std::size_t n)
    : state_(std::make_shared<State>()) {
    if (!n) {
        n = detect_host_topology().logical_threads;
    }
    if (!n) {
        n = 1;
    }

    workers_.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        workers_.emplace_back([this, i] {
            for (;;) {
                std::function<void(std::size_t)> job;
                {
                    std::unique_lock lk(state_->m);
                    state_->cv.wait(lk, [this] {
                        return stopping_.load() || !state_->q.empty();
                    });

                    if (stopping_ && state_->q.empty()) {
                        return;
                    }

                    job = std::move(state_->q.front());
                    state_->q.pop();
                }

                if (job) {
                    job(i);
                }
            }
        });
    }
}

ChimeraCorePool::~ChimeraCorePool() {
    stop();
}

void ChimeraCorePool::submit(std::function<void(std::size_t)> job) {
    if (stopping_) {
        throw std::runtime_error("core pool stopped");
    }

    {
        std::lock_guard lk(state_->m);
        state_->q.push(std::move(job));
    }
    state_->cv.notify_one();
}

void ChimeraCorePool::stop() {
    if (stopping_.exchange(true)) {
        return;
    }

    state_->cv.notify_all();
    for (auto& t : workers_) {
        if (t.joinable()) {
            t.join();
        }
    }
}

} 
