#include "neurovisual_state.hpp"
#include <cmath>
int main() {
  using namespace chimera::neurovisual;
  State14 input{};
  input.value.fill(0.5f);
  input[Axis::energy] = 0.8f;
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
  return std::isfinite(theme.accent_hue_degrees) ? 0 : 5;
}
