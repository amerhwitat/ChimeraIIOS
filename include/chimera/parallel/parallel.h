#pragma once
#include <cstddef>
#include <functional>
namespace chimera::parallel {
enum class Strategy { Task, Data, Tensor, Pipeline, Graph, Distributed, Speculative };
struct Workload { Strategy strategy{Strategy::Task}; std::size_t items{0}; unsigned workers{1}; bool deterministic{true}; bool networked{false}; };
class Executor { public: explicit Executor(unsigned workers=1); unsigned workers() const noexcept; void parallel_for(std::size_t begin, std::size_t end, const std::function<void(std::size_t)>& fn) const; private: unsigned workers_; };
} // namespace chimera::parallel
