#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/hosted/install-chimera-host.sh

Usage:
  tools/hosted/install-chimera-host.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${CHIMERA_HOST_PREFIX:-$HOME/.local/chimera}"
mkdir -p "$PREFIX/bin"
install -m 0755 "$ROOT/tools/hosted/chimera-host-run.sh" "$PREFIX/bin/chimera-host-run"
install -m 0755 "$ROOT/tools/hosted/chimera-host-detect.sh" "$PREFIX/bin/chimera-host-detect"
echo "Installed Chimera II hosted launchers in $PREFIX/bin"
