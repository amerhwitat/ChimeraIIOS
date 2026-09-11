#include <cassert>
#include "chimera/universal_isa.hpp"
int main() {
    using namespace chimera::universal_isa;
    assert(find_target("x86-64") != nullptr);
    assert(find_target("chimera-r8192") != nullptr);
    const auto e = encode_native(0x0001, 1, 2, 3, 0x1122334455667788ULL, 1);
    assert(e.bytes[0] == 0x01 && e.bytes[1] == 0x00);
    assert(e.bytes[2] == 0x01 && e.bytes[4] == 0x02 && e.bytes[6] == 0x03);
    assert(e.length == 16);
    return 0;
}
