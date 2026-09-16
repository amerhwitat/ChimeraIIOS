#include "chimera/dashboard/dashboard.h"
#include <cassert>
int main() {
    using namespace chimera::dashboard;
    assert(classify(20, 75, 90) == HealthState::Healthy);
    assert(classify(80, 75, 90) == HealthState::Degraded);
    assert(classify(95, 75, 90) == HealthState::Critical);
    auto s = collect("desktop");
    assert(s.edition == "desktop");
    assert(!s.kpis.empty());
    return 0;
}
