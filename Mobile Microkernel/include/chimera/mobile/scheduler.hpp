#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class ClusterClass : std::uint8_t { Efficiency, Performance, Prime };

struct CpuState {
    std::uint32_t id{};
    ClusterClass cluster{ClusterClass::Efficiency};
    std::uint32_t capacity{1024};
    std::uint32_t thermal_headroom{1024};
    std::uint32_t frequency_khz{};
    bool online{true};
};

class EnergyAwareScheduler {
public:
    static std::uint32_t score(const CpuState& cpu, std::uint32_t utilization) noexcept {
        if (!cpu.online) return 0;
        const std::uint32_t thermal = cpu.thermal_headroom;
        const std::uint32_t capacity = cpu.capacity ? cpu.capacity : 1;
        return (capacity * thermal) / (utilization + 1);
    }
};

} // namespace chimera::mobile
