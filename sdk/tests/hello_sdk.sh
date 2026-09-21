#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$ROOT/examples/python/hello_chimera.py"
if command -v gcc >/dev/null 2>&1; then
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  gcc -I"$ROOT/include" "$ROOT/examples/c/hello_chimera.c" "$ROOT/src/chimera_sdk.cpp" -lstdc++ -o "$TMP/hello"
  "$TMP/hello"
fi
