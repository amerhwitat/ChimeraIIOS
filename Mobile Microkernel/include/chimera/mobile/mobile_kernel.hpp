#pragma once
#include <cstdint>

namespace chimera::mobile {

struct BootInfo {
    std::uint64_t physical_memory_bytes{};
    std::uint32_t cpu_count{};
    std::uint32_t flags{};
};

struct KernelConfig {
    std::uint32_t quantum_us{1000};
    std::uint32_t idle_poll_us{100};
    bool energy_aware{true};
    bool thermal_aware{true};
};

class MobileKernel {
public:
    explicit MobileKernel(KernelConfig config = {});
    bool initialize(const BootInfo& boot);
    void scheduler_tick(std::uint64_t now_ns);
    void enter_idle();
    void resume();
    const KernelConfig& config() const noexcept { return config_; }

private:
    KernelConfig config_;
    bool initialized_{false};
};

} // namespace chimera::mobile
