#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/emulators/bin/aurora-emulator-window.sh

Usage:
  aurora/emulators/bin/aurora-emulator-window.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu

# Aurora native emulator window bridge.
# Jasper/boot code may select an emulator before the graphical session exists.
# In that case queue the request; aurora-session.sh consumes it after the
# graphical environment is ready. This prevents SDL/OpenGL/Wayland emulators
# from starting successfully as headless processes with no visible window.
ID=${1:?emulator id required}
shift
TITLE=${CHIMERA_EMULATOR_TITLE:-$ID}
RUNDIR=${XDG_RUNTIME_DIR:-/run/chimera}
QUEUE_DIR=${CHIMERA_EMULATOR_QUEUE_DIR:-$RUNDIR/chimera/emulators}
LOG_DIR=${CHIMERA_EMULATOR_LOG_DIR:-$RUNDIR/chimera/emulators/log}
mkdir -p "$QUEUE_DIR" "$LOG_DIR"

has_gui=0
if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]; then
    has_gui=1
elif [ -n "${DISPLAY:-}" ]; then
    has_gui=1
fi

if [ "$has_gui" -ne 1 ]; then
    printf '%s\n' "$ID" > "$QUEUE_DIR/pending"
    printf '%s\n' "$TITLE" > "$QUEUE_DIR/title"
    printf '%s\n' "$*" > "$QUEUE_DIR/args"
    printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) queued $ID" >> "$LOG_DIR/launcher.log"
    echo "Aurora emulator queued until graphical session is ready: $ID"
    exit 0
fi

case "${CHIMERA_EMULATOR_VIDEO:-auto}" in
    wayland) export SDL_VIDEODRIVER=wayland ;;
    x11) export SDL_VIDEODRIVER=x11 ;;
    auto)
        if [ -n "${WAYLAND_DISPLAY:-}" ]; then
            export SDL_VIDEODRIVER=wayland
        elif [ -n "${DISPLAY:-}" ]; then
            export SDL_VIDEODRIVER=x11
        fi
        ;;
esac

export CHIMERA_EMULATOR_ID="$ID"
export CHIMERA_EMULATOR_TITLE="$TITLE"
export CHIMERA_EMULATOR_WINDOW=1
export CHIMERA_EMULATOR_PARENT=aurora
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) launching $ID" >> "$LOG_DIR/launcher.log"
exec "$@"
