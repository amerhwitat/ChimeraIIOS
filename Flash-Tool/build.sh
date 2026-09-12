#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$ROOT/build"
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE="${1:-Release}"
cmake --build "$BUILD" --parallel
printf '[FLASH][DONE] Build complete: %s\n' "$BUILD/chimera_flash_tool"
