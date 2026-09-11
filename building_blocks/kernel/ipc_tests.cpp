#include "ipc_contract.hpp"
#include <cassert>

int main() {
    chimera::kernel::Capability c{42, chimera::kernel::CapabilityType::Ipc,
                                  chimera::kernel::Read | chimera::kernel::Write, 1};
    assert(c.valid());
    assert(c.allows(chimera::kernel::Read));
    assert(!c.allows(chimera::kernel::Grant));
    chimera::kernel::IpcMessage m{7, 42, 16, 0};
    assert(m.sender == 7 && m.endpoint == 42 && m.length == 16);
}
