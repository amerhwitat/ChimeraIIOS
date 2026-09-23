#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_DESKTOP_BUILD_DIR:-$ROOT/build/desktop}"
CXX="${CXX:-g++}"
mkdir -p "$OUT/bin" "$OUT/python" "$OUT/manifests"

if [[ -f "$ROOT/desktop/aurora/aurora-launcher.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/aurora-launcher.cpp" -o "$OUT/bin/aurora-launcher"
fi

# Build the platform-neutral input/event and locale layers. These objects are
# consumed by the Wayland compositor and can also be linked by other shells.
for src in aurora_input aurora_input_router; do
  if [[ -f "$ROOT/desktop/aurora/input/$src.cpp" ]]; then
    "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/input"       -c "$ROOT/desktop/aurora/input/$src.cpp" -o "$OUT/$src.o"
  fi
done
if [[ -f "$ROOT/desktop/aurora/i18n/aurora_locale.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/i18n"     -c "$ROOT/desktop/aurora/i18n/aurora_locale.cpp" -o "$OUT/aurora_locale.o"
fi

if [[ -f "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/neural/cpp"     "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" -o "$OUT/bin/chimera-neural-chat"
fi
if [[ -f "$ROOT/desktop/aurora/apps/aurora_peripherals.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/apps/aurora_peripherals.cpp" -o "$OUT/bin/aurora-peripherals"
fi
if [[ -f "$ROOT/voice/cpp/src/voiceconnect.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/voice/cpp/src/voiceconnect.cpp" -o "$OUT/bin/voiceconnect"
fi

while IFS= read -r -d '' py; do
  python3 -m py_compile "$py"
done < <(find "$ROOT/desktop" -type f -name '*.py' -print0)

cp -a "$ROOT/desktop/aurora" "$OUT/aurora-source"
cp -a "$ROOT/desktop/aurora/gates_menu.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/platform_personality_model.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/session_profiles.json" "$OUT/manifests/" 2>/dev/null || true
cat > "$OUT/manifests/desktop-build-manifest.json" <<EOF
{
  "schema": "CHM-DESKTOP-BUILD-2",
  "aurora": "Wayland Glass",
  "native_binaries": ["bin/aurora-launcher","bin/chimera-neural-chat","bin/voiceconnect","bin/aurora-peripherals","bin/aurora-input-selftest"],
  "native_objects": ["aurora_input.o","aurora_input_router.o","aurora_locale.o"],
  "source_tree": "aurora-source",
  "personalities": ["chimera","linux","unix","windows","macos","bsd"],
  "input": ["mouse","keyboard","touch","tablet","HID","IME","context-menu"],
  "internationalization": ["Unicode","BCP-47","RTL","LTR","logical-start-end"],
  "note": "Desktop personality profiles are compatibility layers; no proprietary Windows or macOS implementation is copied."
}
EOF
printf 'Desktop build artifacts: %s\n' "$OUT"
