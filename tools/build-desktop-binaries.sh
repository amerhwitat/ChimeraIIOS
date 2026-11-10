#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-desktop-binaries.sh

Usage:
  tools/build-desktop-binaries.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_DESKTOP_BUILD_DIR:-$ROOT/build/desktop}"
CXX="${CXX:-g++}"
mkdir -p "$OUT/bin" "$OUT/python" "$OUT/manifests"
if [[ -f "$ROOT/desktop/aurora/aurora-launcher.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/aurora-launcher.cpp" -o "$OUT/bin/aurora-launcher"
fi
for src in aurora_input aurora_input_router; do
  if [[ -f "$ROOT/desktop/aurora/input/$src.cpp" ]]; then
    "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/input" -c "$ROOT/desktop/aurora/input/$src.cpp" -o "$OUT/$src.o"
  fi
done
for src in aurora_locale aurora_utf aurora_emoji; do
  if [[ -f "$ROOT/desktop/aurora/i18n/$src.cpp" ]]; then
    "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/i18n" -c "$ROOT/desktop/aurora/i18n/$src.cpp" -o "$OUT/$src.o"
  fi
done
if [[ -f "$ROOT/desktop/aurora/icons/chimera_icons.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/icons" -c "$ROOT/desktop/aurora/icons/chimera_icons.cpp" -o "$OUT/chimera_icons.o"
fi
if [[ -f "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/neural/cpp" "$ROOT/desktop/aurora/apps/chimera_neural_chat.cpp" -o "$OUT/bin/chimera-neural-chat"
fi
if [[ -f "$ROOT/desktop/aurora/apps/aurora_settings.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/apps/aurora_settings.cpp" -o "$OUT/bin/aurora-settings"
fi
if [[ -f "$ROOT/desktop/aurora/apps/aurora_peripherals.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/desktop/aurora/apps/aurora_peripherals.cpp" -o "$OUT/bin/aurora-peripherals"
fi
if [[ -f "$ROOT/voice/cpp/src/voiceconnect.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra "$ROOT/voice/cpp/src/voiceconnect.cpp" -o "$OUT/bin/voiceconnect"
fi
if [[ -f "$ROOT/userland/commands/chm-utf8.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/i18n" "$ROOT/userland/commands/chm-utf8.cpp" "$ROOT/desktop/aurora/i18n/aurora_utf.cpp" "$ROOT/desktop/aurora/i18n/aurora_emoji.cpp" -o "$OUT/bin/chm-utf8"
fi
if [[ -f "$ROOT/desktop/aurora/i18n/aurora_utf_selftest.cpp" ]]; then
  "$CXX" -std=c++20 -O2 -Wall -Wextra -I"$ROOT/desktop/aurora/i18n" "$ROOT/desktop/aurora/i18n/aurora_utf_selftest.cpp" "$ROOT/desktop/aurora/i18n/aurora_utf.cpp" "$ROOT/desktop/aurora/i18n/aurora_emoji.cpp" -o "$OUT/bin/aurora-utf-selftest"
  "$OUT/bin/aurora-utf-selftest"
fi
while IFS= read -r -d '' py; do python3 -m py_compile "$py"; done < <(find "$ROOT/desktop" -type f -name '*.py' -print0)
cp -a "$ROOT/desktop/aurora" "$OUT/aurora-source"
# Keep transient Python bytecode out of the reusable desktop bundle.
find "$OUT/aurora-source" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
cp -a "$ROOT/desktop/aurora/gates_menu.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/platform_personality_model.json" "$OUT/manifests/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/session_profiles.json" "$OUT/manifests/" 2>/dev/null || true
cat > "$OUT/manifests/desktop-build-manifest.json" <<EOF
{
  "schema": "CHM-DESKTOP-BUILD-3",
  "aurora": "Wayland Glass",
  "native_binaries": ["bin/aurora-launcher","bin/chimera-neural-chat","bin/voiceconnect","bin/aurora-peripherals","bin/aurora-settings","bin/chm-utf8"],
  "native_objects": ["aurora_input.o","aurora_input_router.o","aurora_locale.o","aurora_utf.o","aurora_emoji.o","chimera_icons.o"],
  "source_tree": "aurora-source",
  "internationalization": ["UTF-8","Unicode","BCP-47","CLDR-oriented","RTL","LTR","combining-marks","variation-selectors","emoji","logical-start-end"],
  "icons": {"provider":"native","fallback":"hardcoded-svg","emoji":true},
  "personalities": ["chimera","linux","unix","windows","macos","bsd"],
  "input": ["mouse","keyboard","touch","tablet","HID","IME","context-menu"],
  "note": "Compatibility personalities are clean-room models; no proprietary Windows or macOS implementation is copied."
}
EOF
python3 - "$ROOT" "$OUT" <<'PYDESKTOPSTATUS'
import json,sys
from pathlib import Path
root,out=map(Path,sys.argv[1:])
checks={
 "aurora-launcher":("desktop/aurora/aurora-launcher.cpp","bin/aurora-launcher"),
 "chimera-neural-chat":("desktop/aurora/apps/chimera_neural_chat.cpp","bin/chimera-neural-chat"),
 "aurora-settings":("desktop/aurora/apps/aurora_settings.cpp","bin/aurora-settings"),
 "aurora-peripherals":("desktop/aurora/apps/aurora_peripherals.cpp","bin/aurora-peripherals"),
 "voiceconnect":("voice/cpp/src/voiceconnect.cpp","bin/voiceconnect"),
 "chm-utf8":("userland/commands/chm-utf8.cpp","bin/chm-utf8"),
 "aurora-utf-selftest":("desktop/aurora/i18n/aurora_utf_selftest.cpp","bin/aurora-utf-selftest"),
}
results={}
for name,(source,artifact) in checks.items():
    src=(root/source).is_file()
    built=(out/artifact).is_file()
    state="PASS" if src and built else ("SKIP" if not src else "BLOCKED")
    results[name]={"status":state,"source":source,"artifact":artifact}
for name,source,artifact in [
 ("aurora-input","desktop/aurora/input/aurora_input.cpp","aurora_input.o"),
 ("aurora-input-router","desktop/aurora/input/aurora_input_router.cpp","aurora_input_router.o"),
 ("aurora-locale","desktop/aurora/i18n/aurora_locale.cpp","aurora_locale.o"),
 ("aurora-utf","desktop/aurora/i18n/aurora_utf.cpp","aurora_utf.o"),
 ("aurora-emoji","desktop/aurora/i18n/aurora_emoji.cpp","aurora_emoji.o"),
 ("chimera-icons","desktop/aurora/icons/chimera_icons.cpp","chimera_icons.o"),
]:
    src=(root/source).is_file()
    built=(out/artifact).is_file()
    state="PASS" if src and built else ("SKIP" if not src else "BLOCKED")
    results[name]={"status":state,"source":source,"artifact":artifact}
py_sources=list((root/"desktop").rglob("*.py"))
py_artifacts=list((root/"desktop").rglob("*.pyc"))
py_ok=bool(py_sources) and bool(py_artifacts)
results["desktop-python"]={"status":"PASS" if py_ok else ("SKIP" if not py_sources else "BLOCKED"),"sources":len(py_sources),"compiled_files":len(py_artifacts)}
overall="BLOCKED" if any(v["status"]=="BLOCKED" for v in results.values()) else "PASS"
(out/"manifests/application-build-status.json").write_text(json.dumps({"schema":"CHM-APPLICATION-BUILD-STATUS-1","overall":overall,"results":results},indent=2,sort_keys=True)+"\n",encoding="utf-8")
PYDESKTOPSTATUS
printf 'Desktop build artifacts: %s\n' "$OUT"
