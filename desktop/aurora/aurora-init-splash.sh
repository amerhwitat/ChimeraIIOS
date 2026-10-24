#!/usr/bin/env bash
# Full-screen Init.mp4 splash with live Koronos progress overlay.
# The video is installed at fixed system paths by the root CMake install rules.
set -Eeuo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: aurora-init-splash [--background|--foreground]"
  echo "Plays the installed Init.mp4 with progress read from /run/chimera/koronos-progress.state."
  exit 0
fi

MODE="${1:---foreground}"
VIDEO="${CHIMERA_INIT_VIDEO:-}"
for candidate in "${VIDEO:-/nonexistent}" \
  /boot/chimera/Init.mp4 \
  /usr/share/chimera/aurora/assets/library/Init.mp4 \
  /usr/share/chimera/aurora/assets/Init.mp4 \
  /usr/share/chimera/boot/Init.mp4; do
  if [[ -n "$candidate" && -s "$candidate" ]]; then VIDEO="$candidate"; break; fi
done
[[ -n "$VIDEO" && -s "$VIDEO" ]] || { echo "Aurora splash: Init.mp4 not installed; skipping video." >&2; exit 0; }

PROGRESS="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}"
OSD="${CHIMERA_PROGRESS_OSD:-/usr/share/chimera/aurora/aurora-progress-osd.lua}"
RUNTIME="${XDG_RUNTIME_DIR:-/run}"
PID_FILE="${RUNTIME%/}/chimera-aurora-splash.pid"
MAX_SECONDS="${CHIMERA_SPLASH_MAX_SECONDS:-30}"

if [[ "$MODE" == "--background" ]]; then
  nohup "$0" --foreground >/dev/null 2>&1 </dev/null &
  exit 0
fi

read_percent() {
  [[ -r "$PROGRESS" ]] || { printf '%s' '-1'; return 0; }
  local line
  line="$(grep -E '^percent=[0-9]+' "$PROGRESS" | tail -n 1 || true)"
  if [[ "$line" =~ ^percent=([0-9]+) ]]; then printf '%s' "${BASH_REMATCH[1]}"; return 0; fi
  line="$(tail -n 1 "$PROGRESS" 2>/dev/null || true)"
  if [[ "$line" =~ ^([0-9]+)\| ]]; then printf '%s' "${BASH_REMATCH[1]}"; return 0; fi
  printf '%s' '-1'
}

cleanup() {
  if [[ -r "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    [[ "$pid" =~ ^[0-9]+$ ]] && kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
}
trap cleanup EXIT INT TERM

if command -v mpv >/dev/null 2>&1; then
  args=(--fs --no-terminal --really-quiet --keep-open=no --osd-level=3
        --title='Chimera II OS — Aurora')
  [[ -r "$OSD" ]] && args+=(--script="$OSD")
  mpv "${args[@]}" "$VIDEO" >/dev/null 2>&1 &
  player_pid=$!
  printf '%s\n' "$player_pid" > "$PID_FILE"
elif command -v ffplay >/dev/null 2>&1; then
  # ffplay is a visual fallback only; live OSD requires mpv.
  ffplay -fs -autoexit -loglevel quiet -window_title 'Chimera II OS — Aurora' "$VIDEO" >/dev/null 2>&1 &
  player_pid=$!
  printf '%s\n' "$player_pid" > "$PID_FILE"
else
  echo "Aurora splash: neither mpv nor ffplay is available; skipping video." >&2
  exit 0
fi

start="$(date +%s)"
while kill -0 "$player_pid" 2>/dev/null; do
  percent="$(read_percent)"
  [[ "$percent" == "100" ]] && break
  now="$(date +%s)"
  (( now - start >= MAX_SECONDS )) && break
  sleep 0.25
done
