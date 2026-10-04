#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/initialize-accounts.sh

Usage:
  tools/initialize-accounts.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
if [ "$(id -u)" -ne 0 ]; then echo "initialize-accounts: run as root" >&2; exit 77; fi
ROOT=${CHIMERA_SYSROOT:-}
export CHIMERA_SYSROOT="$ROOT"
chm-user-setup init
if [ "${CHIMERA_CREATE_ROOT:-1}" = 1 ]; then chm-user-setup create-root; fi
echo "Chimera local account database initialized."
