#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export CHIMERA_REPO_ROOT="$ROOT"
export CHIMERA_AURORA_BACKGROUND="${CHIMERA_AURORA_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-desktop.svg}"
export CHIMERA_AURORA_INSTALLER_BACKGROUND="${CHIMERA_AURORA_INSTALLER_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-installer.svg}"
export CHIMERA_AURORA_LIBRARY_BACKGROUND="${CHIMERA_AURORA_LIBRARY_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-library.svg}"
export CHIMERA_NBIT_STATE="$HOME/.config/chimera/nbit-mode.json"
export CHIMERA_NBIT_SOCKET="$XDG_RUNTIME_DIR/chimera/nbit.sock"
export CHIMERA_NEURAL_STATE="$HOME/.config/chimera/neural-dimension.json"
mkdir -p "$(dirname "$CHIMERA_NBIT_SOCKET")"
if command -v python3 >/dev/null 2>&1 && [ -f "$ROOT/tools/runtime/chimera-nbitd.py" ] && [ ! -S "$CHIMERA_NBIT_SOCKET" ]; then
  python3 "$ROOT/tools/runtime/chimera-nbitd.py" >/tmp/chimera-nbitd.log 2>&1 &
fi
PROFILE="${CHIMERA_DESKTOP_PROFILE:-chimera-modern}"
SHELL_ID="${CHIMERA_SHELL:-chimera}"
STATUS="$("$ROOT/tools/runtime/chimera-nbit-mode.py" get 2>/dev/null || printf '{"width":8192,"style":"RISC","execution":"NativeWide"}')"
NEURAL_STATUS="$("$ROOT/tools/runtime/chimera-neural-dim.py" get 2>/dev/null || printf '{"dimensions":1024,"representation":"HyperDimensional","learning":"AdaptiveTensor"}')"
printf 'Aurora Wayland Glass: profile=%s shell=%s | CHIMERA II ISA %s | NEURAL %s\n' "$PROFILE" "$SHELL_ID" "$STATUS" "$NEURAL_STATUS"
# Restore the user's last display mode when the compositor is ready.
if [ "${CHIMERA_DISPLAY_RESTORE:-1}" = "1" ] && command -v chimera-display >/dev/null 2>&1; then
  chimera-display apply-saved >/tmp/chimera-display-restore.log 2>&1 || true
fi
if [ "${CHIMERA_AURORA_NBIT_PANEL:-1}" = "1" ] && [ -x "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" ]; then
  "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" >/tmp/chimera-aurora-nbit-panel.log 2>&1 &
fi
if [ -x "$ROOT/userland/shell/chimera-shell" ]; then
  exec "$ROOT/userland/shell/chimera-shell" -i
fi
exec "${SHELL:-bash}" -i
