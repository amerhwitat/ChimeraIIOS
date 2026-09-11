#include "chimera/memory_bus.hpp"
#include <cassert>
using namespace chimera::memory;
int main() {
    auto profile = VirtualMemoryBus::profile_for("aarch64");
    assert(profile && profile->address_bits > 32);
    VirtualMemoryBus bus(BusSnapshot{*profile, 1024, 256, 128, 8, 2, 0, 0});
    assert(bus.add_region({0x1000, 0x1000, RegionKind::Ram, 0}));
    uint64_t seen = 0;
    assert(bus.add_region({0x2000, 0x100, RegionKind::Mmio, 0}, [&](const BusTransaction& t){ seen=t.value; return BusResult{true, 0x55, 0}; }));
    assert(bus.transact({0x1000, 8, Access::Read, Endianness::Little, Ordering::AcquireRelease, 0}).ok);
    assert(bus.transact({0x2000, 4, Access::Write, Endianness::Little, Ordering::AcquireRelease, 0xAA}).value == 0x55);
    assert(seen == 0xAA);
    assert(!bus.transact({0x3000, 4, Access::Read, Endianness::Little, Ordering::Relaxed, 0}).ok);
    assert(!bus.transact({~uint64_t{0}-1, 8, Access::Read, Endianness::Little, Ordering::Relaxed, 0}).ok);
    return 0;
}
