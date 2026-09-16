#include "chimera/virtualization/cvel.h"
#include <cassert>
#include <iostream>

int main() {
    using namespace chimera::virtualization;
    Manager m;
    auto caps = m.detect_all();
    assert(caps.size() == 3);
    assert(Manager::supports_architecture(caps[0], "x86_64"));
    assert(Manager::supports_architecture(caps[0], "riscv64"));
    assert(!Manager::supports_architecture(caps[1], "riscv64"));
    MachineProfile p{"chimera-test", "x86_64", "generic", 2048, "guest.img", "uefi", false, true};
    QemuBackend q;
    auto cmd = q.build_run_command(p, ExecutionMode::HardwareAssisted);
    assert(cmd.executable == "qemu-system-x86_64");
    assert(!cmd.arguments.empty());
    std::cout << "CVEL tests passed\n";
    return 0;
}
