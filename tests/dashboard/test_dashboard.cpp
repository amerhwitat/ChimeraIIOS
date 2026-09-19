#include "chimera/dashboard/dashboard.h"
#include <algorithm>
#include <cassert>

int main() {
    using namespace chimera::dashboard;
    assert(classify(20, 75, 90) == HealthState::Healthy);
    assert(classify(80, 75, 90) == HealthState::Degraded);
    assert(classify(95, 75, 90) == HealthState::Critical);
    const auto editions = supported_editions();
    assert(editions.size() == 6);
    assert(std::find(editions.begin(), editions.end(), "desktop") != editions.end());
    assert(std::find(editions.begin(), editions.end(), "server") != editions.end());
    assert(std::find(editions.begin(), editions.end(), "mobile") != editions.end());
    assert(std::find(editions.begin(), editions.end(), "edge") != editions.end());
    assert(std::find(editions.begin(), editions.end(), "iot") != editions.end());
    assert(std::find(editions.begin(), editions.end(), "cvel") != editions.end());
    auto s = collect("desktop");
    assert(s.edition == "desktop");
    assert(!s.kpis.empty());
    return 0;
}
