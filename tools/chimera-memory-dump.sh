#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-memory-dump.sh

Usage:
  tools/chimera-memory-dump.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
OUT=${1:-/var/crash/chimera/manual-$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$OUT"
if [ -r /proc/kcore ] && [ "$(id -u 2>/dev/null || echo 1)" = 0 ]; then dd if=/proc/kcore of="$OUT/memory.kcore" bs=1M status=none 2>/dev/null || true; else cat /proc/meminfo > "$OUT/memory.map"; printf 'Physical RAM dumping requires a privileged native kernel crash-dump provider.\n' > "$OUT/memory.note"; fi
printf '%s\n' "$OUT"
