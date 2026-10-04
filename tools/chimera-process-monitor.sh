#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-process-monitor.sh

Usage:
  tools/chimera-process-monitor.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
INTERVAL="${CHIMERA_MONITOR_INTERVAL:-1}"
LOG="${CHIMERA_LOG_FILE:-/var/log/mesgs}"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
echo "CHIMERA II OS — REAL-TIME PROCESS / LOG MONITOR"
while :; do
  clear
  printf 'Chimera II OS | %s | load: ' "$(date '+%Y-%m-%d %H:%M:%S')"
  uptime 2>/dev/null | sed 's/.*load average: /load average: /' || true
  echo
  printf '%-7s %-7s %-7s %-10s %-10s %-s\n' PID CPU STATE TIME COMMAND
  if command -v ps >/dev/null 2>&1; then
    ps -eo pid=,psr=,stat=,etime=,comm= 2>/dev/null | head -n 40 || true
  elif [[ -d /proc ]]; then
    for p in /proc/[0-9]*; do
      pid="${p##*/}"
      comm="$(cat "$p/comm" 2>/dev/null || echo '?')"
      printf '%-7s %-7s %-7s %-10s %-10s %-s\n' "$pid" '-' '-' '-' '-' "$comm"
    done | head -n 40
  fi
  echo
  echo "---------------- CHIMERA LIVE LOG ----------------"
  if [[ -f "$LOG" ]]; then tail -n 18 "$LOG"; else echo "Waiting for $LOG"; fi
  sleep "$INTERVAL"
done
