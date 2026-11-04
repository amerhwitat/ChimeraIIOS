#pragma once
#include <array>
#include <atomic>
#include <cstddef>
namespace chimera {
template<class T,std::size_t N> class SpscRing {
    std::array<T,N> q_{}; std::atomic<std::size_t> head_{0},tail_{0};
public:
    bool push(const T& v){ auto h=head_.load(std::memory_order_relaxed), n=(h+1)%N; if(n==tail_.load(std::memory_order_acquire)) return false; q_[h]=v; head_.store(n,std::memory_order_release); return true; }
    bool pop(T& v){ auto t=tail_.load(std::memory_order_relaxed); if(t==head_.load(std::memory_order_acquire)) return false; v=q_[t]; tail_.store((t+1)%N,std::memory_order_release); return true; }
};
}
