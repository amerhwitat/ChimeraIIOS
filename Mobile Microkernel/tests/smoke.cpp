#include "chimera/mobile/mobile_kernel.hpp"
#include "chimera/mobile/scheduler.hpp"
#include "chimera/mobile/capabilities.hpp"
#include <cassert>

int main() {
    chimera::mobile::MobileKernel kernel;
    chimera::mobile::BootInfo boot{1024ull * 1024ull * 1024ull, 4, 0};
    assert(kernel.initialize(boot));

    chimera::mobile::CpuState cpu{0, chimera::mobile::ClusterClass::Performance, 2048, 900, 1800000, true};
    assert(chimera::mobile::EnergyAwareScheduler::score(cpu, 500) > 0);

    chimera::mobile::Capability cap{1, chimera::mobile::CapabilityType::Ipc,
                                    chimera::mobile::Read, 1};
    assert(cap.valid());
    return 0;
}
