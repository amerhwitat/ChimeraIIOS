#!/bin/sh
set -eu
LOG="${CHIMERA_LOG_FILE:-/var/log/mesgs}"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
: > "$LOG" 2>/dev/null || true
printf '\033[2J\033[H'
echo "CHIMERA II OS — BOOT / INSTALL / RUNTIME LOG"
echo "Live process activity follows below."
echo
if command -v tail >/dev/null 2>&1; then
  exec tail -n 28 -F "$LOG"
fi
exec sh
