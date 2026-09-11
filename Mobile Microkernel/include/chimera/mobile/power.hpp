#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class PowerState : std::uint8_t { Active, Idle, Suspend, Hibernate };

struct ThermalState {
    std::uint32_t temperature_mc{};
    std::uint32_t throttle_threshold_mc{85000};
    bool throttling() const noexcept { return temperature_mc >= throttle_threshold_mc; }
};

class PowerManager {
public:
    void set_state(PowerState state) noexcept { state_ = state; }
    PowerState state() const noexcept { return state_; }
    void update_thermal(ThermalState state) noexcept { thermal_ = state; }
    const ThermalState& thermal() const noexcept { return thermal_; }

private:
    PowerState state_{PowerState::Active};
    ThermalState thermal_{};
};

} // namespace chimera::mobile
