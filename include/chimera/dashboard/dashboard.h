#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace chimera::dashboard {

enum class HealthState { Unknown, Healthy, Degraded, Critical };

struct Kpi {
    std::string name;
    double value{0.0};
    std::string unit;
    double warning{0.0};
    double critical{0.0};
    HealthState state{HealthState::Unknown};
};

struct Snapshot {
    std::string edition;
    std::string architecture;
    std::uint64_t uptime_seconds{0};
    std::vector<Kpi> kpis;
};

Snapshot collect(const std::string& edition);
HealthState classify(double value, double warning, double critical);
std::string state_name(HealthState state);

} // namespace chimera::dashboard
