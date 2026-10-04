#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-init-splash.sh

Usage:
  desktop/aurora/aurora-init-splash.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIDEO="${CHIMERA_INIT_VIDEO:-$ROOT/assets/init.mp4}"
PROGRESS="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}"
PID_FILE="${XDG_RUNTIME_DIR:-/run}/chimera-aurora-splash.pid"
MAX_SECONDS="${CHIMERA_SPLASH_MAX_SECONDS:-15}"

read_percent(){
  [[ -f "$PROGRESS" ]] && sed -n 's/^percent=//p' "$PROGRESS" | tail -1 || printf '%s' '-1'
}

play_video(){
  [[ -s "$VIDEO" ]] || return 2
  if command -v mpv >/dev/null 2>&1; then
    mpv --fs --no-terminal --really-quiet --keep-open=no "$VIDEO" >/dev/null 2>&1 & echo $! > "$PID_FILE"; return 0
  fi
  if command -v ffplay >/dev/null 2>&1; then
    ffplay -fs -autoexit -loglevel quiet "$VIDEO" >/dev/null 2>&1 & echo $! > "$PID_FILE"; return 0
  fi
  return 2
}

cleanup(){
  if [[ -f "$PID_FILE" ]]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; rm -f "$PID_FILE"; fi
}
trap cleanup EXIT INT TERM
play_video || exit 0
start="$(date +%s)"
while :; do
  p="$(read_percent)"
  [[ "$p" == 100 ]] && break
  now="$(date +%s)"
  (( now - start >= MAX_SECONDS )) && break
  sleep 0.25
done
