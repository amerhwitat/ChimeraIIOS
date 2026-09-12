#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$ROOT/engine/CMakeLists.txt" ]]; then
  cmake -S "$ROOT/engine" -B "$ROOT/build/gcc" -DCMAKE_BUILD_TYPE="${1:-Release}"
  cmake --build "$ROOT/build/gcc" --parallel
else
  echo "[ISO][INFO] No engine CMakeLists.txt; use language-specific builders under python/, java/, dotnet/ and vcpp/."
fi
