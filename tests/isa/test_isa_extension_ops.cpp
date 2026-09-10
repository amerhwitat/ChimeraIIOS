#include <cassert>
#include "chimera/isa_extension_ops.hpp"

int main() {
    chimera::Register8192 a(0x10), b(0x03);
    assert(chimera::isa::clz64(a.lane(0)) == 59);
    assert(chimera::isa::ctz64(a.lane(0)) == 4);
    assert(chimera::isa::popcnt64(a.lane(0)) == 1);

    const auto add = chimera::isa::vector_add(a, b);
    assert(add.lane(0) == 0x13);

    const auto madd = chimera::isa::vector_madd(a, b, chimera::Register8192(2));
    assert(madd.lane(0) == 0x32);

    assert(chimera::isa::crc32(0, 0x12345678) != 0);
    assert(chimera::isa::has_extension("BITMANIP"));
    assert(chimera::isa::has_extension("ATOMICS"));
    assert(chimera::isa::has_extension("VECTOR"));
    return 0;
}
