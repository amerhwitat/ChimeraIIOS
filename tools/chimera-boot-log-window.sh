#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-boot-log-window.sh

Usage:
  tools/chimera-boot-log-window.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
