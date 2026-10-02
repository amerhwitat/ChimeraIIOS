#!/usr/bin/env bash
set -Eeuo pipefail

# Aurora pointer feedback: visual pressed state + click sound.
# Called by the compositor/input integration with PRESS/RELEASE and optional
# button number. It remains non-critical: missing sound tooling never blocks UI.
STATE_DIR="${XDG_RUNTIME_DIR:-/tmp}/chimera-aurora"
STATE_FILE="$STATE_DIR/mouse.state"
SOUND="${AURORA_CLICK_SOUND:-/usr/share/chimera/aurora/sounds/mouse-click.wav}"
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
      fi
    fi
    ;;
  RELEASE|release|released|*)
    printf 'state=normal\nbutton=%s\n' "$button" > "$STATE_FILE"
    ;;
esac
