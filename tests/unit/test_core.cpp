#include <cassert>
#include <cstdint>
#include <string>
#include "chimera/RegisterN.hpp"
#include "chimera/state128.hpp"

int main() {
    chimera::RegisterN<8192> a{};
    chimera::RegisterN<8192> b{};
    a.set_u64(0, 0xffffffffffffffffULL);
    b.set_u64(0, 1ULL);
    auto c = a + b;
    assert(c.lane(0) == 0);
    assert(c.lane(1) == 1);

    chimera::State128 s{};
    s[0] = 1.0;
    s[127] = 2.0;
    auto y = chimera::state_transition(s, s);
    assert(y[0] == 2.0);
    assert(y[127] == 4.0);
    return 0;
}
