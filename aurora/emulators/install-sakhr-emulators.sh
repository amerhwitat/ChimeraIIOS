#!/usr/bin/env bash
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
