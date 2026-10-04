#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-driver-center.sh

Usage:
  tools/chimera-driver-center.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
CMD=\${1:-search}
case "$CMD" in
  search|update) exec /usr/bin/chimera-driver-manager.sh search;;
  inventory) exec /usr/bin/chimera-driver-manager.sh inventory;;
  download) shift; exec /usr/bin/chimera-driver-manager.sh download "$@";;
  install) shift; exec /usr/bin/chimera-driver-manager.sh install "$@";;
  *) echo "Usage: chimera-driver-center {search|update|inventory|install FILE}"; exit 2;;
esac
