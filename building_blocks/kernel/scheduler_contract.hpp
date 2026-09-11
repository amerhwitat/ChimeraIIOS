#pragma once
#include <cstdint>
#include <limits>

namespace chimera::kernel {

enum class Priority : std::uint8_t { Idle, Normal, Realtime };

struct TaskBudget {
    std::uint64_t period_us{};
    std::uint64_t budget_us{};
    Priority priority{Priority::Normal};
};

constexpr bool valid(const TaskBudget& b) noexcept {
    return b.period_us != 0 && b.budget_us != 0 && b.budget_us <= b.period_us;
}

class SchedulerContract {
public:
    constexpr bool admission(const TaskBudget& b) const noexcept {
        if (!valid(b)) return false;
        return utilization_ + static_cast<double>(b.budget_us) / b.period_us <= 1.0;
    }
    constexpr void account(const TaskBudget& b) noexcept {
        if (valid(b)) utilization_ += static_cast<double>(b.budget_us) / b.period_us;
    }
    constexpr double utilization() const noexcept { return utilization_; }
private:
    double utilization_{};
};

} // namespace chimera::kernel
