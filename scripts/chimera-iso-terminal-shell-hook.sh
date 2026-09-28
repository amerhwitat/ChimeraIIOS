#!/usr/bin/env bash
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
