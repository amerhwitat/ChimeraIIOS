#include "memory_contract.hpp"
#include <cassert>

int main() {
    chimera::memory::PageRange r{0x1000, 4};
    assert(r.end() == 0x5000);
    chimera::memory::DmaDescriptor d{0x2000, 4096, chimera::memory::Read | chimera::memory::Interrupt, 0};
    assert(chimera::memory::valid(d));
    chimera::memory::DmaDescriptor bad{};
    assert(!chimera::memory::valid(bad));
}
