#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-mobile-binaries.sh

Usage:
  tools/build-mobile-binaries.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${CHIMERA_MOBILE_BUILD_DIR:-$ROOT/build/mobile}"
SRC="$ROOT/mobile/runtime/chimera_mobile_init.c"
mkdir -p "$OUT/bin"
build_one(){ local cc="$1" out="$2"; command -v "$cc" >/dev/null 2>&1 || return 1; "$cc" -O2 -static "$SRC" -o "$out" 2>/dev/null || "$cc" -O2 "$SRC" -o "$out"; chmod +x "$out"; }
build_one gcc "$OUT/bin/chimera-mobile-init-x86_64" || true
build_one aarch64-linux-gnu-gcc "$OUT/bin/chimera-mobile-init-arm64" || true
build_one arm-linux-gnueabihf-gcc "$OUT/bin/chimera-mobile-init-armv7" || true
cp "$ROOT/mobile/runtime/chimera_mobile_init.c" "$OUT/bin/"
printf '{"schema":"CHM-MOBILE-BINARIES-1","x86_64":"chimera-mobile-init-x86_64","arm64":"chimera-mobile-init-arm64","armv7":"chimera-mobile-init-armv7","cross_compile_when_toolchains_are_present":true}\n' > "$OUT/manifests/mobile-binaries.json"
