#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace chimera::neural {

struct DimensionProfile {
    std::size_t dimensions{1024};
    std::size_t min_dimensions{128};
    std::size_t max_dimensions{65536};
    std::size_t active_dimensions{1024};
    std::string representation{"HyperDimensional"};
    std::string learning{"AdaptiveTensor"};
};

class HyperVector {
public:
    explicit HyperVector(std::size_t dimensions = 1024);
    HyperVector(std::size_t dimensions, std::span<const float> values);

    std::size_t dimensions() const noexcept { return values_.size(); }
    std::span<float> values() noexcept { return values_; }
    std::span<const float> values() const noexcept { return values_; }

    void normalize() noexcept;
    float cosine(const HyperVector& other) const;
    static HyperVector bind(const HyperVector& a, const HyperVector& b);
    static HyperVector bundle(const std::vector<std::reference_wrapper<const HyperVector>>& vectors);

private:
    std::vector<float> values_;
};

class DeepDimensionEngine {
public:
    explicit DeepDimensionEngine(DimensionProfile profile = {});

    const DimensionProfile& profile() const noexcept { return profile_; }
    bool set_dimensions(std::size_t dimensions) noexcept;
    HyperVector encode(std::span<const float> input) const;
    HyperVector project(const HyperVector& input, std::size_t target_dimensions) const;

private:
    DimensionProfile profile_;
};

} // namespace chimera::neural
