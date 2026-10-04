#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: sdk/java/build.sh

Usage:
  sdk/java/build.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname "$0")" && pwd)"
OUT="$ROOT/build/classes"
rm -rf "$OUT" "$ROOT/chimera-sdk.jar"
mkdir -p "$OUT"
javac -d "$OUT" "$ROOT"/src/org/chimera/sdk/*.java
jar --create --file "$ROOT/chimera-sdk.jar" -C "$OUT" .
