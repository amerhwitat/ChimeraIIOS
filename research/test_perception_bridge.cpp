#include "perception_bridge.hpp"
#include <array>
#include <iostream>
#include <limits>

using namespace chimera::perception;
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL line " << __LINE__ << ": " #x "\n"; return 1; } } while (0)

int main() {
    Budget b;
    for (std::size_t n : {1u, 127u, 128u, 129u, 256u, 512u, 1024u, 8192u}) {
        FeatureVector v;
        CHECK(FeatureVector::allocate(n, b, v) == Error::ok);
        CHECK(v.values.size() == n);
    }
    FeatureVector bad;
    CHECK(FeatureVector::allocate(0, b, bad) == Error::invalid_argument);
    CHECK(FeatureVector::allocate(8193, b, bad) == Error::budget_exceeded);
    Budget tiny; tiny.max_vector_bytes = 16;
    CHECK(FeatureVector::allocate(5, tiny, bad) == Error::budget_exceeded);

    std::array<std::uint8_t, 24> pixels{};
    FrameView good{pixels.data(), pixels.size(), 4, 2, 12, 3};
    CHECK(good.validate(b) == Error::ok);
    FrameView bad_stride{pixels.data(), pixels.size(), 4, 2, 11, 3};
    CHECK(bad_stride.validate(b) == Error::invalid_frame);
    FrameView truncated{pixels.data(), 23, 4, 2, 12, 3};
    CHECK(truncated.validate(b) == Error::invalid_frame);
    FrameView null_frame{nullptr, 24, 4, 2, 12, 3};
    CHECK(null_frame.validate(b) == Error::invalid_frame);
    FrameView huge{pixels.data(), pixels.size(), 8192, 8192, 0xffffffffu, 4};
    CHECK(huge.validate(b) != Error::ok);

    CapabilityTable caps;
    CHECK(caps.grant(77, 9, scope_bit(Scope::capture) | scope_bit(Scope::infer)) == Error::ok);
    CHECK(caps.authorize(77, 9, Scope::capture) == Error::ok);
    CHECK(caps.authorize(77, 10, Scope::capture) == Error::permission_denied);
    CHECK(caps.authorize(77, 9, Scope::ocr) == Error::permission_denied);
    CHECK(caps.revoke(77, 9) == Error::ok);
    CHECK(caps.authorize(77, 9, Scope::capture) == Error::revoked);
    CHECK(caps.grant(0, 9, 1) == Error::invalid_argument);
    std::cout << "PERCEPTION BRIDGE SAFETY TESTS PASS\n";
    return 0;
}
