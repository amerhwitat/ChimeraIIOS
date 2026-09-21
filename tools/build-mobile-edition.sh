#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_MOBILE_BUILD_DIR:-$ROOT/build/mobile}"
mkdir -p "$OUT/bin" "$OUT/source" "$OUT/manifests"
cp "$ROOT/config/foreign-runtime-sources.json" "$OUT/manifests/"
if [[ -d "$ROOT/build/foreign/source/AOSP" ]]; then cp -a "$ROOT/build/foreign/source/AOSP" "$OUT/source/"; fi
if [[ -d "$ROOT/build/foreign/source/LineageOS" ]]; then cp -a "$ROOT/build/foreign/source/LineageOS" "$OUT/source/"; fi
if [[ -d "$ROOT/build/foreign/source/Plasma_Mobile" ]]; then cp -a "$ROOT/build/foreign/source/Plasma_Mobile" "$OUT/source/"; fi
cat > "$OUT/manifests/mobile-edition.json" <<'EOF'
{"schema":"CHM-MOBILE-EDITION-1","architectures":["arm64-v8a","armeabi-v7a","x86_64"],"editions":["Chimera Mobile","Aurora Mobile","Plasma Mobile compatibility"],"source_stage":"source","binary_stage":"bin","policy":"build-from-source-or-licensed-redistributable-only"}
EOF
printf 'Mobile edition scaffold: %s\n' "$OUT"
