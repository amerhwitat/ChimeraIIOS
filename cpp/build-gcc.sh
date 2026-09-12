#!/usr/bin/env bash
set -euo pipefail
CONFIG="${1:-Release}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/gcc"
echo "[CHIMERA][DEPENDENCY] gcc=$(command -v gcc || echo missing)"
echo "[CHIMERA][DEPENDENCY] g++=$(command -v g++ || echo missing)"
echo "[CHIMERA][DEPENDENCY] cmake=$(command -v cmake || echo missing)"
echo "[CHIMERA][CONFIGURE] $CONFIG"
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE="$CONFIG" -DCMAKE_C_COMPILER="${CC:-gcc}" -DCMAKE_CXX_COMPILER="${CXX:-g++}"
echo "[CHIMERA][COMPILE][LINK]"
cmake --build "$BUILD" --parallel "$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
echo "[CHIMERA][TEST]"
ctest --test-dir "$BUILD" --output-on-failure
echo "[CHIMERA][DONE] GCC build completed."
