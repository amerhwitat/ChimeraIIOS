#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: scripts/import-aurora-terminal-shell-suite.sh

Usage:
  scripts/import-aurora-terminal-shell-suite.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CHIMERA_ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:-${ROOT}/build/iso/rootfs}"
export CHIMERA_TERMINAL_CACHE="${CHIMERA_TERMINAL_CACHE:-${ROOT}/build/terminal-cache}"
export CHIMERA_SHELL_CACHE="${CHIMERA_SHELL_CACHE:-${ROOT}/build/shell-cache}"
mkdir -p "$CHIMERA_ROOTFS_DIR/usr/share/chimera/aurora"
printf '[AURORA] Importing terminal suite...\n'
bash "$ROOT/scripts/import-aurora-terminal-suite.sh"
printf '[AURORA] Importing shell suite...\n'
bash "$ROOT/scripts/import-aurora-shell-suite.sh"
printf '[AURORA] Terminal and shell suite staged in %s\n' "$CHIMERA_ROOTFS_DIR"
