#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/shells/launch-shell.sh

Usage:
  aurora/shells/launch-shell.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
shell="${1:-bash}"
case "$shell" in
  bash|zsh|fish|dash|mksh|yash|elvish) exec "$shell" ;;
  nu|nushell) exec nu ;;
  *) echo "Unknown Chimera shell: $shell" >&2; exit 2 ;;
esac
