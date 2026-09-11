#include "chimera/memory_bus_probe.hpp"
#include <cassert>
using namespace chimera::memory;
int main() {
    auto ok = inspect_bus(ProbeInput{"x86-64",64,64,Endianness::Little,Ordering::AcquireRelease,64,true,true,true,4096,1024,512,16,1,0,0});
    assert(ok && ok->profile.architecture == "x86-64");
    assert(!inspect_bus(ProbeInput{"",64,64,Endianness::Little,Ordering::Relaxed,64,true,false,false,0,0,0,1,1,0,0}));
    assert(!inspect_bus(ProbeInput{"x86-64",65,64,Endianness::Little,Ordering::Relaxed,64,true,false,false,0,0,0,1,1,0,0}));
    return 0;
}
