#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${ROOT}/build/hosted-linux"
cmake -S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=HOSTED
cmake --build "$BUILD" --parallel "${CMAKE_BUILD_PARALLEL_LEVEL:-2}"
ctest --test-dir "$BUILD" --output-on-failure || true
printf 'Hosted Linux build complete: %s\n' "$BUILD"
