#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace chimera::neurovisual {
enum class Axis : std::size_t {
  x, y, z, time, perspective, energy, interaction, identity,
  material, information, stochasticity, agency, semantic, integration, count
};
inline constexpr std::size_t axis_count = static_cast<std::size_t>(Axis::count);
struct State14 {
  std::array<float, axis_count> value{};
  float &operator[](Axis axis) { return value[static_cast<std::size_t>(axis)]; }
  float operator[](Axis axis) const { return value[static_cast<std::size_t>(axis)]; }
};
struct DimensionNode {
  Axis axis;
  float value;
  std::vector<std::shared_ptr<DimensionNode>> children;
};
struct ThemeProjection {
  float accent_hue_degrees;
  float glass_opacity;
  float glass_blur_px;
  float motion_scale;
  float information_density;
  float brightness;
  float parallax_px;
  float glow_strength;
  float spatial_x_px;
  float spatial_y_px;
  float depth_offset_px;
  float interaction_glow;
  float temporal_accent_alpha;
};
inline float bounded(float v) { return std::clamp(std::isfinite(v) ? v : 0.5f, 0.0f, 1.0f); }

// A small recurrent/temporal smoother. The upstream CNN/LLM adapter may supply
// normalized features, but this core never claims to infer consciousness,
// quantum probabilities, or scientific ground truth.
class RecurrentState {
 public:
  explicit RecurrentState(float alpha = 0.18f) : alpha_(std::clamp(alpha, 0.02f, 0.8f)) {
    state_.value.fill(0.5f);
  }
  const State14 &update(const State14 &input) {
    for (std::size_t i = 0; i < axis_count; ++i)
      state_.value[i] = bounded(state_.value[i] + (bounded(input.value[i]) - state_.value[i]) * alpha_);
    return state_;
  }
  const State14 &state() const { return state_; }
 private:
  float alpha_;
  State14 state_{};
};
inline ThemeProjection project_theme(const State14 &s, float base_hue = 184.0f) {
  const auto v = [&s](Axis a) { return bounded(s[a]); };
  return {
    base_hue + (v(Axis::semantic) - 0.5f) * 54.0f + (v(Axis::perspective) - 0.5f) * 20.0f,
    0.48f + v(Axis::material) * 0.34f,
    10.0f + v(Axis::material) * 22.0f,
    0.15f + v(Axis::agency) * 0.85f,
    0.82f + v(Axis::information) * 0.34f,
    0.82f + v(Axis::energy) * 0.36f,
    1.0f + v(Axis::perspective) * 5.0f,
    0.08f + v(Axis::integration) * 0.22f,
    (v(Axis::x) - 0.5f) * 8.0f,
    (v(Axis::y) - 0.5f) * 8.0f,
    (v(Axis::z) - 0.5f) * 12.0f,
    v(Axis::interaction) * 0.22f,
    0.12f + v(Axis::time) * 0.16f
  };
}
inline std::shared_ptr<DimensionNode> make_dimension_tree(const State14 &s) {
  auto root = std::make_shared<DimensionNode>(DimensionNode{Axis::integration, bounded(s[Axis::integration]), {}});
  for (std::size_t i = 0; i < axis_count; ++i) {
    const auto axis = static_cast<Axis>(i);
    if (axis == Axis::integration) continue;
    root->children.push_back(std::make_shared<DimensionNode>(DimensionNode{axis, bounded(s[axis]), {}}));
  }
  return root;
}
} // namespace chimera::neurovisual
