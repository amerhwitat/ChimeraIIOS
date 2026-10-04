#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: build-chimera-iso-aurora.sh

Usage:
  build-chimera-iso-aurora.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CHIMERA_AURORA_ASSET="${CHIMERA_AURORA_ASSET:-$ROOT/boot/visual/aurora-wayland-glass.jpg}"
export CHIMERA_AURORA_BACKGROUND_JPG="${CHIMERA_AURORA_BACKGROUND_JPG:-$ROOT/boot/visual/aurora-wayland-glass.jpg}"

if [[ ! -s "$ROOT/boot/visual/aurora-wayland-glass.jpg" ]]; then
  STAGE="$ROOT/build/embedded-aurora"
  rm -rf "$STAGE"
  CHIMERA_TARGET_ROOT="$STAGE" bash "$ROOT/tools/branding/install-aurora-background.sh"
  mkdir -p "$ROOT/boot/visual"
  cp -f "$STAGE/boot/visual/aurora-wayland-glass.jpg" "$ROOT/boot/visual/aurora-wayland-glass.jpg"
fi

bash "$ROOT/boot/validate-boot-assets.sh" "$ROOT"
exec bash "$ROOT/build-chimera-iso.sh" --background "$CHIMERA_AURORA_ASSET" "$@"
