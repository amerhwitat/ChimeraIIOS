#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-mouse-click.sh

Usage:
  desktop/aurora/aurora-mouse-click.sh [PRESS|RELEASE] [button]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  Updates Aurora's pointer pressed-state marker. On PRESS, plays the
  redistributable menu-select sound when a supported audio player is present.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

# Aurora pointer feedback: visual pressed state + click sound.
# Called by the compositor/input integration with PRESS/RELEASE and optional
# button number. It remains non-critical: missing sound tooling never blocks UI.
STATE_DIR="${XDG_RUNTIME_DIR:-/tmp}/chimera-aurora"
STATE_FILE="$STATE_DIR/mouse.state"
# Use the sound that is actually shipped in the Aurora asset manifest.
SOUND="${AURORA_CLICK_SOUND:-/usr/share/chimera/aurora/assets/sounds/menu-select.wav}"
mkdir -p "$STATE_DIR"

state="${1:-RELEASE}"
button="${2:-left}"

case "$state" in
  PRESS|press|pressed)
    printf 'state=pressed\nbutton=%s\n' "$button" > "$STATE_FILE"
    if [[ -r "$SOUND" ]]; then
      if command -v paplay >/dev/null 2>&1; then paplay "$SOUND" >/dev/null 2>&1 &
      elif command -v pw-play >/dev/null 2>&1; then pw-play "$SOUND" >/dev/null 2>&1 &
      elif command -v aplay >/dev/null 2>&1; then aplay -q "$SOUND" >/dev/null 2>&1 &
      elif command -v ffplay >/dev/null 2>&1; then ffplay -nodisp -autoexit -loglevel quiet "$SOUND" >/dev/null 2>&1 &
      fi
    fi
    ;;
  RELEASE|release|released|*)
    printf 'state=normal\nbutton=%s\n' "$button" > "$STATE_FILE"
    ;;
esac
