#include "chimera/neural/hyperdimensional.hpp"
#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <functional>
#include <utility>

namespace chimera::neural {

HyperVector::HyperVector(std::size_t dimensions) : values_(dimensions, 0.0F) {
    if (dimensions < 1) throw std::invalid_argument("hypervector dimensions must be positive");
}
HyperVector::HyperVector(std::size_t dimensions, std::span<const float> values) : HyperVector(dimensions) {
    std::copy_n(values.begin(), std::min(values.size(), values_.size()), values_.begin());
}
void HyperVector::normalize() noexcept {
    double sum = 0.0;
    for (float x : values_) sum += static_cast<double>(x) * x;
    const double norm = std::sqrt(sum);
    if (norm == 0.0) return;
    for (float& x : values_) x = static_cast<float>(x / norm);
}
float HyperVector::cosine(const HyperVector& other) const {
    if (dimensions() != other.dimensions()) throw std::invalid_argument("hypervector dimensions differ");
    double dot = 0.0, aa = 0.0, bb = 0.0;
    for (std::size_t i = 0; i < dimensions(); ++i) {
        dot += static_cast<double>(values_[i]) * other.values_[i];
        aa += static_cast<double>(values_[i]) * values_[i];
        bb += static_cast<double>(other.values_[i]) * other.values_[i];
    }
    if (aa == 0.0 || bb == 0.0) return 0.0F;
    return static_cast<float>(dot / std::sqrt(aa * bb));
}
HyperVector HyperVector::bind(const HyperVector& a, const HyperVector& b) {
    if (a.dimensions() != b.dimensions()) throw std::invalid_argument("hypervector dimensions differ");
    HyperVector out(a.dimensions());
    for (std::size_t i = 0; i < out.dimensions(); ++i) out.values_[i] = a.values_[i] * b.values_[i];
    return out;
}
HyperVector HyperVector::bundle(const std::vector<std::reference_wrapper<const HyperVector>>& vectors) {
    if (vectors.empty()) throw std::invalid_argument("cannot bundle empty hypervector set");
    const auto dimensions = vectors.front().get().dimensions();
    HyperVector out(dimensions);
    for (const auto& ref : vectors) {
        if (ref.get().dimensions() != dimensions) throw std::invalid_argument("hypervector dimensions differ");
        for (std::size_t i = 0; i < dimensions; ++i) out.values_[i] += ref.get().values_[i];
    }
    out.normalize();
    return out;
}
DeepDimensionEngine::DeepDimensionEngine(DimensionProfile profile) : profile_(std::move(profile)) {
    if (profile_.min_dimensions < 128 || profile_.min_dimensions > profile_.max_dimensions ||
        profile_.active_dimensions < profile_.min_dimensions || profile_.active_dimensions > profile_.max_dimensions)
        throw std::invalid_argument("invalid deep-dimensional profile");
}
bool DeepDimensionEngine::set_dimensions(std::size_t dimensions) noexcept {
    if (dimensions < profile_.min_dimensions || dimensions > profile_.max_dimensions) return false;
    profile_.active_dimensions = dimensions;
    return true;
}
HyperVector DeepDimensionEngine::encode(std::span<const float> input) const {
    HyperVector out(profile_.active_dimensions);
    if (input.empty()) return out;
    for (std::size_t i = 0; i < out.dimensions(); ++i) out.values()[i] = input[i % input.size()];
    out.normalize();
    return out;
}
HyperVector DeepDimensionEngine::project(const HyperVector& input, std::size_t target_dimensions) const {
    if (target_dimensions < profile_.min_dimensions || target_dimensions > profile_.max_dimensions)
        throw std::invalid_argument("target dimensionality outside engine range");
    HyperVector out(target_dimensions);
    for (std::size_t i = 0; i < target_dimensions; ++i) out.values()[i] = input.values()[i % input.dimensions()];
    out.normalize();
    return out;
}

} // namespace chimera::neural
