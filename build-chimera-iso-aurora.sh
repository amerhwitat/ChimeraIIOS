#!/usr/bin/env bash
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
