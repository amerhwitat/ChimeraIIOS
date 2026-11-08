#!/usr/bin/env bash
set -Eeuo pipefail
export XDG_SESSION_TYPE=x11
export XDG_CURRENT_DESKTOP=Aurora
export DESKTOP_SESSION=chimera-aurora-x11
log="${XDG_RUNTIME_DIR:-/tmp}/chimera-aurora-x11.log"
mkdir -p "$(dirname "$log")"
if ! command -v openbox-session >/dev/null 2>&1; then
  echo "Aurora X11 fallback requires the real Openbox session binary." | tee -a "$log" >&2
  exit 127
fi
openbox-session >>"$log" 2>&1 &
wm_pid=$!
cleanup() { kill "$wm_pid" 2>/dev/null || true; wait "$wm_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
sleep 1
if [[ -x /usr/local/bin/aurora-kiosk.py ]]; then
  /usr/local/bin/aurora-kiosk.py >>"$log" 2>&1
elif command -v xterm >/dev/null 2>&1; then
  xterm -title "Aurora Desktop — X11 fallback" >>"$log" 2>&1
else
  echo "Aurora shell kiosk and xterm are both unavailable." | tee -a "$log" >&2
  exit 127
fi
