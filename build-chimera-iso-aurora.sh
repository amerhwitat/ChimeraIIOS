#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Canonical Aurora artwork entrypoint. The main builder already accepts --background;
# this wrapper makes the repository's embedded artwork the non-optional default.
export CHIMERA_AURORA_ASSET="${CHIMERA_AURORA_ASSET:-$ROOT/boot/visual/aurora-wayland-glass.jpg}"
export CHIMERA_AURORA_BACKGROUND_JPG="${CHIMERA_AURORA_BACKGROUND_JPG:-$ROOT/boot/visual/aurora-wayland-glass.jpg}"

if [[ ! -s "$ROOT/boot/visual/aurora-wayland-glass.jpg" ]]; then
  bash "$ROOT/tools/branding/install-aurora-background.sh"
fi

bash "$ROOT/boot/validate-boot-assets.sh" "$ROOT"
exec bash "$ROOT/build-chimera-iso.sh" --background "$CHIMERA_AURORA_ASSET" "$@"
