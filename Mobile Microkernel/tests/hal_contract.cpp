#include "chimera/mobile/hal_contract.hpp"
#include <cassert>

int main() {
    using namespace chimera::mobile;
    CpuFeatures cpu{Architecture::AArch64, 8, true, true, true};
    TimerContract timer{1000000, 100};
    DmaContract dma{0x100000, 4096, 3};
    assert(valid(cpu));
    assert(valid(timer));
    assert(valid(dma));
    assert(PowerState::DeepSuspend != PowerState::Active);
}
