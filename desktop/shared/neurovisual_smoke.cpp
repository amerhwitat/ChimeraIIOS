#include "neurovisual_state.hpp"
#include <cmath>
int main() {
  using namespace chimera::neurovisual;
  State14 input{};
  input.value.fill(0.5f);
  input[Axis::x] = 0.75f;
  input[Axis::y] = 0.25f;
  input[Axis::z] = 0.75f;
  input[Axis::time] = 0.75f;
  input[Axis::energy] = 0.8f;
  input[Axis::interaction] = 0.5f;
  input[Axis::material] = 0.9f;
  input[Axis::agency] = 0.2f;
  RecurrentState recurrent(0.5f);
  const State14 &state = recurrent.update(input);
  const ThemeProjection theme = project_theme(state);
  const auto tree = make_dimension_tree(state);
  if (!tree || tree->children.size() != axis_count - 1) return 1;
  if (!(theme.glass_opacity >= 0.48f && theme.glass_opacity <= 0.82f)) return 2;
  if (!(theme.glass_blur_px >= 10.0f && theme.glass_blur_px <= 32.0f)) return 3;
  if (!(theme.brightness > 1.0f && theme.motion_scale < 0.5f)) return 4;
  if (!(theme.spatial_x_px > 0.9f && theme.spatial_y_px < -0.9f)) return 5;
  if (!(theme.depth_offset_px > 1.4f && theme.interaction_glow > 0.1f)) return 6;
  if (!(theme.temporal_accent_alpha > 0.21f)) return 7;
  return std::isfinite(theme.accent_hue_degrees) ? 0 : 8;
}
