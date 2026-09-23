#include "ChimeraCorePool.h"
#include <condition_variable>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>
#if defined(__linux__)
#include <fstream>
#endif

namespace chimera::arch {
namespace {
struct Queue { std::mutex m; std::condition_variable cv; std::queue<std::function<void(std::size_t)>> q; };
Queue gq;
}
CoreTopology detect_host_topology() {
    const auto logical=std::thread::hardware_concurrency();
    CoreTopology t{logical?logical:1,logical?logical:1,false};
#if defined(__linux__)
    std::ifstream f("/sys/devices/system/cpu/smt/active"); int active=0; if(f>>active) t.smt=active!=0;
#endif
    return t;
}
ChimeraCorePool::ChimeraCorePool(std::size_t logical_cores) {
    if(!logical_cores) logical_cores=detect_host_topology().logical_threads;
    if(!logical_cores) logical_cores=1;
    workers_.reserve(logical_cores);
    for(std::size_t i=0;i<logical_cores;++i) workers_.emplace_back([this,i]{
        for(;;){
            std::function<void(std::size_t)> job;
            { std::unique_lock lk(gq.m); gq.cv.wait(lk,[this]{return stopping_.load()||!gq.q.empty();});
              if(stopping_&&gq.q.empty()) return; job=std::move(gq.q.front()); gq.q.pop(); }
            if(job) job(i);
        }
    });
}
ChimeraCorePool::~ChimeraCorePool(){stop();}
void ChimeraCorePool::submit(std::function<void(std::size_t)> job){ if(stopping_) throw std::runtime_error("core pool stopped"); {std::lock_guard lk(gq.m);gq.q.push(std::move(job));} gq.cv.notify_one(); }
void ChimeraCorePool::stop(){ if(stopping_.exchange(true)) return; gq.cv.notify_all(); for(auto& t:workers_) if(t.joinable()) t.join(); }
}
