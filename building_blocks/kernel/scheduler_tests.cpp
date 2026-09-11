#include "scheduler_contract.hpp"
#include <cassert>

int main() {
    chimera::kernel::TaskBudget a{1000, 250, chimera::kernel::Priority::Normal};
    chimera::kernel::TaskBudget b{1000, 750, chimera::kernel::Priority::Realtime};
    chimera::kernel::SchedulerContract s;
    assert(s.admission(a));
    s.account(a);
    assert(s.admission(b));
    s.account(b);
    assert(s.utilization() <= 1.0 + 1e-12);
    chimera::kernel::TaskBudget bad{100, 101, chimera::kernel::Priority::Normal};
    assert(!s.admission(bad));
}
