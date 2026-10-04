#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-xexec.sh

Usage:
  tools/chimera-xexec.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
PAYLOAD=${1:?compressed payload}; shift
CACHE=/run/chimera/xexec
mkdir -p "$CACHE"
base=$(basename "$PAYLOAD"); out="$CACHE/${base%.*}"
if [ -x "$out" ] && [ "$PAYLOAD" -ot "$out" ]; then exec "$out" "$@"; fi
case "$PAYLOAD" in
  *.zst) command -v zstd >/dev/null 2>&1 || exit 127; zstd -dc "$PAYLOAD" > "$out";;
  *.xz) command -v xz >/dev/null 2>&1 || exit 127; xz -dc "$PAYLOAD" > "$out";;
  *.gz) command -v gzip >/dev/null 2>&1 || exit 127; gzip -dc "$PAYLOAD" > "$out";;
  *) exit 2;;
esac
chmod 700 "$out"
exec "$out" "$@"
