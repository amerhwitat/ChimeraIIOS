#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export CHIMERA_REPO_ROOT="$ROOT"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
SYSTEM_AURORA_BACKGROUND="/usr/share/chimera/aurora/ChimeraIIOS-Aurora-Wayland-Glass.jpg"
BOOT_AURORA_BACKGROUND="/boot/visual/aurora-wayland-glass.jpg"
if [ -r "$SYSTEM_AURORA_BACKGROUND" ]; then
  export CHIMERA_AURORA_BACKGROUND="$SYSTEM_AURORA_BACKGROUND"
elif [ -r "$BOOT_AURORA_BACKGROUND" ]; then
  export CHIMERA_AURORA_BACKGROUND="$BOOT_AURORA_BACKGROUND"
else
  export CHIMERA_AURORA_BACKGROUND="${CHIMERA_AURORA_BACKGROUND:-$ROOT/desktop/aurora/assets/aurora-desktop.svg}"
fi
export CHIMERA_AURORA_BACKGROUND_JPG="$CHIMERA_AURORA_BACKGROUND"
export CHIMERA_AURORA_INSTALLER_BACKGROUND="${CHIMERA_AURORA_INSTALLER_BACKGROUND:-$CHIMERA_AURORA_BACKGROUND}"
export CHIMERA_AURORA_LIBRARY_BACKGROUND="${CHIMERA_AURORA_LIBRARY_BACKGROUND:-$CHIMERA_AURORA_BACKGROUND}"
export CHIMERA_BOOT_ASSET_DIR="${CHIMERA_BOOT_ASSET_DIR:-/boot/visual}"
export CHIMERA_BOOT_VIDEO="${CHIMERA_BOOT_VIDEO:-$CHIMERA_BOOT_ASSET_DIR/chimera-intro.mp4}"
export CHIMERA_BOOT_LOG="${CHIMERA_BOOT_LOG:-/run/chimera/boot.log}"
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
printf 'Aurora Wayland Glass: background=%s profile=%s shell=%s | CHIMERA II ISA %s | NEURAL %s\n' "$CHIMERA_AURORA_BACKGROUND" "$PROFILE" "$SHELL_ID" "$STATUS" "$NEURAL_STATUS"
if [ -x "$ROOT/tools/boot/chimera-boot-visual.sh" ]; then
  "$ROOT/tools/boot/chimera-boot-visual.sh" >/tmp/chimera-boot-visual.log 2>&1 || true
fi
if [ "${CHIMERA_DISPLAY_RESTORE:-1}" = "1" ] && command -v chimera-display >/dev/null 2>&1; then
  chimera-display apply-saved >/tmp/chimera-display-restore.log 2>&1 || true
fi
if [ "${CHIMERA_AURORA_NBIT_PANEL:-1}" = "1" ] && [ -x "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" ]; then
  "$ROOT/desktop/aurora/aurora-nbit-top-panel.sh" >/tmp/chimera-aurora-nbit-panel.log 2>&1 &
fi

# Consume emulator requests selected before Aurora was graphical. Jasper/boot
# entries are allowed to queue a selection; this watcher launches it only after
# Wayland/X11 is available, so native SDL/OpenGL windows become real Aurora
# application windows instead of headless/background processes.
launch_queued_emulator() {
  local q="${CHIMERA_EMULATOR_QUEUE_DIR:-$XDG_RUNTIME_DIR/chimera/emulators}"
  local id launcher
  [ -s "$q/pending" ] || return 0
  id="$(cat "$q/pending")"
  case "$id" in
    sakhr-ax170) launcher="$ROOT/aurora/emulators/bin/launch-sakhr-ax170.sh" ;;
    sakhr-ax230) launcher="$ROOT/aurora/emulators/bin/launch-sakhr-ax230.sh" ;;
    retro-*) launcher="$ROOT/aurora/emulators/bin/launch-retro.sh" ;;
    *) printf '[AURORA] Unknown queued emulator: %s\n' "$id" >> /tmp/chimera-aurora-emulator.log; return 0 ;;
  esac
  if [ -x "$launcher" ]; then
    mv "$q/pending" "$q/active" 2>/dev/null || return 0
    ("$launcher" "$([ "$id" != "sakhr-ax170" ] && [ "$id" != "sakhr-ax230" ] && printf '%s' "$id")" >>/tmp/chimera-aurora-emulator.log 2>&1 || true)
    rm -f "$q/active" "$q/title" "$q/args"
  fi
}
(
  q="${CHIMERA_EMULATOR_QUEUE_DIR:-$XDG_RUNTIME_DIR/chimera/emulators}"
  for _ in $(seq 1 60); do
    if [ -s "$q/pending" ] && { [ -n "${DISPLAY:-}" ] || { [ -n "${WAYLAND_DISPLAY:-}" ] && [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; }; }; then
      launch_queued_emulator
      break
    fi
    sleep 1
  done
) &

if [ -x "$ROOT/userland/shell/chimera-shell" ]; then
  exec "$ROOT/userland/shell/chimera-shell" -i
fi
exec "${SHELL:-bash}" -i
