#include "chimera/mobile/platform.hpp"
#include <cassert>

int main() {
    using namespace chimera::mobile;

    PlatformContract contract{};
    assert(contract.architecture() == MobileArchitecture::Unknown);
    assert(contract.has_required_memory(64ull * 1024ull * 1024ull));
    assert(!contract.has_required_memory(0));

    contract.set_architecture(MobileArchitecture::AArch64);
    contract.set_page_size(4096);
    contract.set_cpu_count(8);
    assert(contract.architecture() == MobileArchitecture::AArch64);
    assert(contract.page_size() == 4096);
    assert(contract.cpu_count() == 8);
    assert(contract.valid());

    return 0;
}
