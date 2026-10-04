#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/emulators/install-sakhr-emulators.sh

Usage:
  aurora/emulators/install-sakhr-emulators.sh [options] [arguments]

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
PREFIX="${1:-/usr/local}"
SHARE="$PREFIX/share/chimera-aurora/emulators"
BIN="$PREFIX/bin/aurora/emulators/bin"
APPS="$PREFIX/share/applications"
mkdir -p "$SHARE" "$BIN" "$APPS"
cp -f "$ROOT/aurora/emulators/emulator-registry.json" "$SHARE/"
cp -f "$ROOT/aurora/emulators/binary-manifest.json" "$SHARE/"
cp -f "$ROOT/aurora/emulators/desktop/"*.desktop "$APPS/"
cp -f "$ROOT/aurora/emulators/bin/"launch-sakhr-*.sh "$BIN/"
chmod 0755 "$BIN"/launch-sakhr-*.sh
printf '%s\n' "Installed Aurora Sakhr emulator panel assets into $PREFIX"
printf '%s\n' "Registry: $SHARE/emulator-registry.json"
printf '%s\n' "Binary manifest: $SHARE/binary-manifest.json"
