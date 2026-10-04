#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-kmsg-forwarder.sh

Usage:
  tools/chimera-kmsg-forwarder.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
LOG=/var/log/mesgs
mkdir -p /var/log/mesgs/archive
touch "$LOG"
if [ -r /dev/kmsg ]; then
  while IFS= read -r line; do
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line" >> "$LOG"
  done < /dev/kmsg
elif [ -r /proc/kmsg ]; then
  while IFS= read -r line; do
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line" >> "$LOG"
  done < /proc/kmsg
else
  printf '%s [KLOG] Kernel message device unavailable; console logging remains active.\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  while :; do sleep 3600; done
fi
