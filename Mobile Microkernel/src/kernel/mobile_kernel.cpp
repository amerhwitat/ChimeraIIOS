#include "chimera/mobile/mobile_kernel.hpp"

namespace chimera::mobile {

MobileKernel::MobileKernel(KernelConfig config) : config_(config) {}

bool MobileKernel::initialize(const BootInfo& boot) {
    initialized_ = boot.cpu_count != 0 && boot.physical_memory_bytes != 0;
    return initialized_;
}

void MobileKernel::scheduler_tick(std::uint64_t) {
    if (!initialized_) return;
    // Scheduling policy is deliberately separated from hardware-specific drivers.
}

void MobileKernel::enter_idle() {
    if (!initialized_) return;
    // Architecture backends provide WFI/WFE or equivalent idle instructions.
}

void MobileKernel::resume() {
    // Resume hooks are supplied by the platform power-management layer.
}

} // namespace chimera::mobile
