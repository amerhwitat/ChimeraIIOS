#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: scripts/chimera-iso-terminal-shell-hook.sh

Usage:
  scripts/chimera-iso-terminal-shell-hook.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
# ISO-build hook for build-chimera-iso.sh.
# Source this hook immediately before the rootfs is packaged into squashfs/ISO.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CHIMERA_ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:?build-chimera-iso.sh must export CHIMERA_ROOTFS_DIR}"
export CHIMERA_TERMINAL_MODE="${CHIMERA_TERMINAL_MODE:-source-first}"
export CHIMERA_SHELL_MODE="${CHIMERA_SHELL_MODE:-source-first}"
export CHIMERA_TERMINAL_CACHE="${CHIMERA_TERMINAL_CACHE:-${BUILD_DIR:-$ROOT/build}/terminal-cache}"
export CHIMERA_SHELL_CACHE="${CHIMERA_SHELL_CACHE:-${BUILD_DIR:-$ROOT/build}/shell-cache}"
mkdir -p "$CHIMERA_ROOTFS_DIR"
bash "$ROOT/scripts/import-aurora-terminal-shell-suite.sh"
bash "$ROOT/aurora/terminals/install-desktop-entries.sh"
# Copy the shell launcher into the image.
install -Dm0755 "$ROOT/aurora/shells/launch-shell.sh" "$CHIMERA_ROOTFS_DIR/usr/lib/chimera/aurora/launch-shell.sh"
printf '[CHIMERA-ISO] Aurora terminal/shell suite staged: %s\n' "$CHIMERA_ROOTFS_DIR"
