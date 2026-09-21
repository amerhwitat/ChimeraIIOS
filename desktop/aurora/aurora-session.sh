#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export CHIMERA_REPO_ROOT="$ROOT"
PROFILE="${CHIMERA_DESKTOP_PROFILE:-chimera-modern}"
SHELL_ID="${CHIMERA_SHELL:-chimera}"
printf 'Aurora Wayland Glass: profile=%s shell=%s\n' "$PROFILE" "$SHELL_ID"
if [ -x "$ROOT/userland/shell/chimera-shell" ]; then
  exec "$ROOT/userland/shell/chimera-shell" -i
fi
exec "${SHELL:-bash}" -i
