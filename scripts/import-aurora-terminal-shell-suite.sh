#!/usr/bin/env bash
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
