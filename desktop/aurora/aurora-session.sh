#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export CHIMERA_REPO_ROOT="$ROOT"
export CHIMERA_AURORA_BACKGROUND="${CHIMERA_AURORA_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-desktop.svg}"
export CHIMERA_AURORA_INSTALLER_BACKGROUND="${CHIMERA_AURORA_INSTALLER_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-installer.svg}"
export CHIMERA_AURORA_LIBRARY_BACKGROUND="${CHIMERA_AURORA_LIBRARY_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-library.svg}"
PROFILE="${CHIMERA_DESKTOP_PROFILE:-chimera-modern}"
SHELL_ID="${CHIMERA_SHELL:-chimera}"
printf 'Aurora Wayland Glass: profile=%s shell=%s\n' "$PROFILE" "$SHELL_ID"
if [ -x "$ROOT/userland/shell/chimera-shell" ]; then
  exec "$ROOT/userland/shell/chimera-shell" -i
fi
exec "${SHELL:-bash}" -i
