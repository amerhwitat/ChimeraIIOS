#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_DESKTOP_BUILD_DIR:-$ROOT/build/desktop}"
CXX="${CXX:-g++}"
mkdir -p "$OUT/bin" "$OUT/python" "$OUT/manifests"

# Build every native Aurora C/C++ executable currently present.  The launcher is
# intentionally host-userland code; Koronos itself remains freestanding.
shopt -s nullglob
native_sources=("$ROOT/desktop"/**/*.cpp)
if [[ -f "$ROOT/desktop/aurora/aurora-launcher.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/aurora-launcher.cpp" -o "$OUT/bin/aurora-launcher"
fi

if [[ -f "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/neural/cpp"     "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" -o "$OUT/bin/chimera-neural-chat"
fi

if [[ -f "$ROOT/voice/cpp/src/voiceconnect.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra     "$ROOT/voice/cpp/src/voiceconnect.cpp" -o "$OUT/bin/voiceconnect"
fi

# Compile Python desktop components to bytecode so the ISO contains both source
# and ready-to-load Python implementations.
while IFS= read -r -d '' py; do
  python3 -m py_compile "$py"
done < <(find "$ROOT/desktop" -type f -name '*.py' -print0)

cp -a "$ROOT/desktop/aurora" "$OUT/aurora-source"
cp -a "$ROOT/desktop/aurora/gates_menu.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/platform_personality_model.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/session_profiles.json" "$OUT/manifests/" 2>/dev/null || true
cat > "$OUT/manifests/desktop-build-manifest.json" <<EOF
{
  "schema": "CHM-DESKTOP-BUILD-1",
  "aurora": "Wayland Glass",
  "native_binaries": ["bin/aurora-launcher"],
  "source_tree": "aurora-source",
  "personalities": ["chimera","linux","unix","windows","macos","bsd"],
  "note": "Desktop personality profiles are packaged implementations/configuration layers; unsupported native GUI backends are not fabricated as completed binaries."
}
EOF
printf 'Desktop build artifacts: %s\n' "$OUT"
