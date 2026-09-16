#include "chimera/dashboard/dashboard.h"
#include <algorithm>
#include <fstream>
#include <string>
#include <thread>

namespace chimera::dashboard {

HealthState classify(double value, double warning, double critical) {
    if (value >= critical) return HealthState::Critical;
    if (value >= warning) return HealthState::Degraded;
    return HealthState::Healthy;
}

std::string state_name(HealthState state) {
    switch (state) {
        case HealthState::Healthy: return "healthy";
        case HealthState::Degraded: return "degraded";
        case HealthState::Critical: return "critical";
        default: return "unknown";
    }
}

static double cpu_load_percent() {
    std::ifstream f("/proc/loadavg");
    double load = 0.0;
    if (!(f >> load)) return 0.0;
    const auto cores = std::max(1u, std::thread::hardware_concurrency());
    return std::min(100.0, (load / static_cast<double>(cores)) * 100.0);
}

static double memory_percent() {
    std::ifstream f("/proc/meminfo");
    std::string key, unit;
    double value = 0.0, total = 0.0, available = 0.0;
    while (f >> key >> value >> unit) {
        if (key == "MemTotal:") total = value;
        else if (key == "MemAvailable:") available = value;
    }
    return total > 0.0 ? ((total - available) / total) * 100.0 : 0.0;
}

Snapshot collect(const std::string& edition) {
    Snapshot s;
    s.edition = edition;
#if defined(__x86_64__) || defined(_M_X64)
    s.architecture = "x86_64";
#elif defined(__aarch64__) || defined(_M_ARM64)
    s.architecture = "arm64";
#elif defined(__riscv) && (__riscv_xlen == 64)
    s.architecture = "riscv64";
#else
    s.architecture = "unknown";
#endif
    s.kpis.push_back({"cpu.utilization", cpu_load_percent(), "%", 75.0, 90.0});
    s.kpis.back().state = classify(s.kpis.back().value, 75.0, 90.0);
    s.kpis.push_back({"memory.utilization", memory_percent(), "%", 80.0, 95.0});
    s.kpis.back().state = classify(s.kpis.back().value, 80.0, 95.0);
    return s;
}

} // namespace chimera::dashboard
