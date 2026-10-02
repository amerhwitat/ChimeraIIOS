#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIDEO="${CHIMERA_INIT_VIDEO:-$ROOT/assets/init.mp4}"
PROGRESS="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}"
PID_FILE="${XDG_RUNTIME_DIR:-/run}/chimera-aurora-splash.pid"

read_percent(){
  [[ -f "$PROGRESS" ]] && sed -n 's/^percent=//p' "$PROGRESS" | tail -1 || printf '%s' '-1'
}

play_video(){
  [[ -s "$VIDEO" ]] || return 0
  if command -v mpv >/dev/null 2>&1; then
    mpv --fs --no-terminal --really-quiet --keep-open=no "$VIDEO" >/dev/null 2>&1 & echo $! > "$PID_FILE"; return 0
  fi
  if command -v ffplay >/dev/null 2>&1; then
    ffplay -fs -autoexit -loglevel quiet "$VIDEO" >/dev/null 2>&1 & echo $! > "$PID_FILE"; return 0
  fi
  return 0
}

cleanup(){
  if [[ -f "$PID_FILE" ]]; then kill "$(cat "$PID_FILE")" 2>/dev/null || true; rm -f "$PID_FILE"; fi
}
trap cleanup EXIT INT TERM
play_video
while :; do
  p="$(read_percent)"
  [[ "$p" == 100 ]] && break
  sleep 0.25
done
