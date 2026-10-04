#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-progress.sh

Usage:
  desktop/aurora/aurora-progress.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

# Unified Aurora progress surface for installer, Live CD, recovery, updates,
# first boot and mobile flashing. State format is:
#   percent|phase|message
# in $CHIMERA_PROGRESS_FILE (default /run/chimera/progress.state).

STATE_FILE="${CHIMERA_PROGRESS_FILE:-/run/chimera/progress.state}"
MODE="${1:-monitor}"

bar(){
  local pct="${1:-0}" width="${2:-32}" filled empty
  ((pct<0)) && pct=0
  ((pct>100)) && pct=100
  filled=$((pct*width/100)); empty=$((width-filled))
  printf '['
  printf '%*s' "$filled" '' | tr ' ' '#'
  printf '%*s' "$empty" '' | tr ' ' '-'
  printf '] %3d%%' "$pct"
}

read_state(){
  local line pct phase msg
  [[ -r "$STATE_FILE" ]] || return 1
  IFS='|' read -r pct phase msg < "$STATE_FILE" || return 1
  [[ "$pct" =~ ^[0-9]+$ ]] || pct=0
  printf '%s\n%s\n%s\n' "$pct" "${phase:-Chimera II OS}" "${msg:-Working...}"
}

render_text(){
  local pct phase msg
  mapfile -t v < <(read_state || printf '0\nAurora\nWaiting for progress state\n')
  pct="${v[0]}"; phase="${v[1]}"; msg="${v[2]}"
  printf '\rAurora | %-24s ' "$phase"
  bar "$pct"
  printf ' | %s' "$msg"
}

render_gui(){
  command -v zenity >/dev/null 2>&1 || return 1
  zenity --progress \
    --title='Chimera II OS — Aurora Progress' \
    --text='Starting...' \
    --percentage=0 \
    --auto-close \
    --no-cancel \
    --width=720 < <(
      while :; do
        if mapfile -t v < <(read_state 2>/dev/null); then
          pct="${v[0]}"; phase="${v[1]}"; msg="${v[2]}"
          printf '%s\n# %s — %s\n' "$pct" "$phase" "$msg"
          [ "$pct" -ge 100 ] && break
        fi
        sleep 1
      done
    )
}

case "$MODE" in
  set)
    pct="${2:-0}"; phase="${3:-Aurora}"; msg="${4:-Working...}"
    mkdir -p "$(dirname "$STATE_FILE")"
    printf '%s|%s|%s\n' "$pct" "$phase" "$msg" > "$STATE_FILE"
    ;;
  text)
    while :; do render_text; sleep 1; done
    ;;
  gui)
    render_gui || { echo '[Aurora] zenity unavailable; using text progress.' >&2; exec "$0" text; }
    ;;
  monitor)
    if command -v zenity >/dev/null 2>&1 && [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
      exec "$0" gui
    fi
    exec "$0" text
    ;;
  *)
    echo "Usage: $0 {set PERCENT PHASE MESSAGE|text|gui|monitor}" >&2
    exit 2
    ;;
esac
