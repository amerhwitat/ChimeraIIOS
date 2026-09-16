#include "chimera/performance/performance.h"
#include <algorithm>

namespace chimera::performance {

HostProfile Advisor::host_profile(unsigned hardware_threads) noexcept {
    const unsigned threads = std::max(1u, hardware_threads);
    return {threads, std::max(1u, threads > 2 ? threads - 1 : threads), true};
}

OptimizationHints Advisor::suggest(WorkloadClass workload, unsigned hardware_threads) noexcept {
    const auto host = host_profile(hardware_threads);
    OptimizationHints h{};
    h.workers = host.recommended_workers;
    switch (workload) {
        case WorkloadClass::IO:
            h.prefer_async_io = true;
            h.prefer_zero_copy = true;
            h.rationale = "I/O workloads benefit from bounded asynchronous and buffer reuse paths";
            break;
        case WorkloadClass::Memory:
        case WorkloadClass::AI:
        case WorkloadClass::Database:
            h.prefer_zero_copy = true;
            h.rationale = "memory movement is a primary optimization target";
            break;
        case WorkloadClass::Network:
            h.prefer_async_io = true;
            h.rationale = "network work should avoid blocking worker threads";
            break;
        default:
            h.rationale = "bounded host concurrency with native target guidance";
            break;
    }
    return h;
}

const char* Advisor::workload_name(WorkloadClass workload) noexcept {
    switch (workload) {
        case WorkloadClass::General: return "general";
        case WorkloadClass::Compute: return "compute";
        case WorkloadClass::IO: return "io";
        case WorkloadClass::Memory: return "memory";
        case WorkloadClass::AI: return "ai";
        case WorkloadClass::Database: return "database";
        case WorkloadClass::Network: return "network";
    }
    return "unknown";
}

} // namespace chimera::performance
