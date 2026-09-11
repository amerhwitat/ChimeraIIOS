#include "chimera/nbit_runtime.hpp"
#include <cassert>
#include <cstdint>

using chimera::runtime::WideInt;
using chimera::runtime::Width;

static WideInt value(std::uint64_t lo, std::uint64_t hi = 0) {
    const std::uint64_t limbs[] = {lo, hi};
    return WideInt(Width{128}, limbs);
}

int main() {
    const auto a = value(0x0000000000000000ULL, 0x0000000000000001ULL);
    const auto b = value(0x0000000000000001ULL, 0x0000000000000000ULL);

    // These operations are part of the R8192 0x01-0x09 arithmetic/bitwise group.
    const auto sub = WideInt::sub(a, b);
    assert(sub.limbs()[0] == 0xffffffffffffffffULL);
    assert(sub.limbs()[1] == 0x0000000000000000ULL);

    const auto band = WideInt::bit_and(value(0xf0f0), value(0x0ff0));
    assert(band.limbs()[0] == 0x00f0ULL);

    const auto bor = WideInt::bit_or(value(0xf000), value(0x000f));
    assert(bor.limbs()[0] == 0xf00fULL);

    const auto shr = WideInt::shr(value(0x0000000000000000ULL, 0x1), 64);
    assert(shr.limbs()[0] == 1ULL);
    assert(shr.limbs()[1] == 0ULL);

    return 0;
}
