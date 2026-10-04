#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: sdk/tests/hello_sdk.sh

Usage:
  sdk/tests/hello_sdk.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$ROOT/examples/python/hello_chimera.py"
if command -v gcc >/dev/null 2>&1; then
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  gcc -I"$ROOT/include" "$ROOT/examples/c/hello_chimera.c" "$ROOT/src/chimera_sdk.cpp" -lstdc++ -o "$TMP/hello"
  "$TMP/hello"
fi
