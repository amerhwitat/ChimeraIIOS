#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-session.sh

Usage:
  desktop/aurora/aurora-session.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d /usr/share/chimera/aurora ]; then
  ROOT=/usr/share/chimera
else
  ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
export CHIMERA_REPO_ROOT="$ROOT"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Runtime artwork is staged by tools/stage-chimera-runtime.sh. Keep the boot
# visual fallback for live/recovery environments where /usr/share is absent.
for bg in \
  "$ROOT/aurora/aurora-wayland-glass.png" \
  "/boot/visual/aurora-wayland-glass.png" \
  "$ROOT/desktop/aurora/assets/aurora-desktop.svg"; do
  if [ -r "$bg" ]; then
    export CHIMERA_AURORA_BACKGROUND="$bg"
    break
  fi
done

export CHIMERA_AURORA_BACKGROUND="${CHIMERA_AURORA_BACKGROUND:-$ROOT/aurora/aurora-wayland-glass.png}"
export CHIMERA_AURORA_BACKGROUND_JPG="$CHIMERA_AURORA_BACKGROUND"
export CHIMERA_AURORA_INSTALLER_BACKGROUND="${CHIMERA_AURORA_INSTALLER_BACKGROUND:-$CHIMERA_AURORA_BACKGROUND}"
export CHIMERA_AURORA_LIBRARY_BACKGROUND="${CHIMERA_AURORA_LIBRARY_BACKGROUND:-$CHIMERA_AURORA_BACKGROUND}"
export CHIMERA_BOOT_ASSET_DIR="${CHIMERA_BOOT_ASSET_DIR:-/boot/visual}"
export CHIMERA_BOOT_VIDEO="${CHIMERA_BOOT_VIDEO:-$CHIMERA_BOOT_ASSET_DIR/chimera-intro.mp4}"
export CHIMERA_BOOT_LOG="${CHIMERA_BOOT_LOG:-/run/chimera/boot.log}"

# Preserve the existing N-bit/neural status hooks when they are present, but
# never make the graphical session depend on research-only helpers.
if [ -x "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" ] && [ "${CHIMERA_AURORA_NBIT_PANEL:-1}" = "1" ]; then
  "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" >/tmp/chimera-aurora-nbit-panel.log 2>&1 &
fi

# The historical script used to terminate in a shell even when invoked as the
# desktop session. The real runtime entrypoint is now the Wayland compositor
# bridge, which gives labwc/Wayland ownership of the graphical session.
if [ -x "$ROOT/aurora/aurora-start.sh" ]; then
  exec "$ROOT/aurora/aurora-start.sh"
fi

printf '%s\n' '[Aurora][ERROR] aurora-start.sh is missing; entering recovery shell.' >&2
exec "${SHELL:-/bin/bash}" -i
