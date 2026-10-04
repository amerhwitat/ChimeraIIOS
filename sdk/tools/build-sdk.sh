#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: sdk/tools/build-sdk.sh

Usage:
  sdk/tools/build-sdk.sh [options] [arguments]

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
BUILD="$ROOT/build"
mkdir -p "$BUILD"
cmake -S "$ROOT/.." -B "$BUILD/cmake-sdk" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_SDK_ONLY=ON
cmake --build "$BUILD/cmake-sdk" --target chimera_sdk chimera-sdk-config --parallel 2
if command -v javac >/dev/null 2>&1 && command -v jar >/dev/null 2>&1; then "$ROOT/java/build.sh"; fi
if command -v dotnet >/dev/null 2>&1; then dotnet build "$ROOT/csharp/Chimera.Sdk.csproj" -c Release; fi
python3 -m compileall -q "$ROOT/python/chimera_sdk"
