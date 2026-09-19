#include "chimera/virtualization/vm.h"
#include <cassert>

int main() {
    using namespace chimera::virtualization;
    VmLifecycle vm;
    assert(vm.state() == VmState::Created);
    assert(vm.start());
    assert(vm.state() == VmState::Running);
    assert(vm.pause());
    assert(vm.state() == VmState::Paused);
    assert(vm.resume());
    assert(vm.state() == VmState::Running);
    assert(vm.stop());
    assert(vm.state() == VmState::Stopped);
    assert(!vm.pause());
    assert(vm.reset());
    assert(vm.state() == VmState::Created);
    return 0;
}
