#pragma once
#include <cstdint>

namespace chimera::mobile {

enum class Architecture : std::uint8_t { AArch64, RiscV64 };
enum class PowerState : std::uint8_t { Active, Idle, Suspend, DeepSuspend, Off };

struct CpuFeatures {
    Architecture architecture{Architecture::AArch64};
    std::uint32_t cpu_count{};
    bool mmu{};
    bool virtualization{};
    bool crypto{};
};

struct TimerContract {
    std::uint64_t frequency_hz{};
    std::uint64_t next_deadline{};
};

struct DmaContract {
    std::uint64_t address{};
    std::uint32_t length{};
    std::uint32_t flags{};
};

constexpr bool valid(const CpuFeatures& f) noexcept {
    return f.cpu_count != 0 && f.mmu;
}
constexpr bool valid(const TimerContract& t) noexcept {
    return t.frequency_hz != 0;
}
constexpr bool valid(const DmaContract& d) noexcept {
    return d.address != 0 && d.length != 0;
}

} // namespace chimera::mobile
