#include "chimera/neural/hyperdimensional.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

int main() {
    chimera::neural::DimensionProfile p{};
    p.active_dimensions = 1024;
    p.max_dimensions = 65536;
    chimera::neural::DeepDimensionEngine engine(p);
    assert(engine.set_dimensions(256));
    assert(engine.set_dimensions(1024));
    assert(engine.set_dimensions(4096));
    assert(engine.set_dimensions(16384));
    assert(!engine.set_dimensions(127));
    assert(engine.set_dimensions(65536));

    const std::vector<float> seed{1.0F, 2.0F, 3.0F, 5.0F, 8.0F};
    auto a = engine.encode(seed);
    auto b = engine.project(a, 16384);
    assert(a.dimensions() == 65536);
    assert(b.dimensions() == 16384);
    assert(std::isfinite(b.cosine(b)));
    std::cout << "Neural hyperdimensional engine: PASS (65536D capable)\n";
}
