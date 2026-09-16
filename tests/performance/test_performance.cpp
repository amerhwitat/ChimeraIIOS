#include "chimera/performance/performance.h"
#include <cassert>
#include <cstring>
int main() {
    using namespace chimera::performance;
    auto one = Advisor::host_profile(0);
    assert(one.hardware_threads == 1 && one.recommended_workers == 1);
    auto many = Advisor::host_profile(8);
    assert(many.recommended_workers >= 1 && many.recommended_workers <= 8);
    auto io = Advisor::suggest(WorkloadClass::IO, 8);
    assert(io.prefer_async_io && io.prefer_zero_copy);
    auto ai = Advisor::suggest(WorkloadClass::AI, 8);
    assert(ai.workers >= 1 && ai.prefer_zero_copy);
    assert(std::strcmp(Advisor::workload_name(WorkloadClass::Database), "database") == 0);
    return 0;
}
