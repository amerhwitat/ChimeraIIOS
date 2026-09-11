#pragma once
#include <cstdint>

namespace chimera::robotics {

enum class VCoreRole : std::uint8_t { MotorControl, Sensor, Safety, Fusion, SlamAi, Network };

struct VCorePartition {
    std::uint16_t id{};
    VCoreRole role{VCoreRole::Sensor};
    std::uint16_t cpu_count{1};
    std::uint32_t period_us{};
    std::uint32_t budget_us{};
};

constexpr bool real_time(const VCorePartition& p) noexcept {
    return p.role == VCoreRole::MotorControl || p.role == VCoreRole::Safety;
}

constexpr bool valid(const VCorePartition& p) noexcept {
    return p.cpu_count != 0 && p.period_us != 0 && p.budget_us != 0 && p.budget_us <= p.period_us;
}

struct SensorSample {
    std::uint64_t timestamp_ns{};
    std::uint32_t sensor_id{};
    std::uint32_t sequence{};
};

} // namespace chimera::robotics
