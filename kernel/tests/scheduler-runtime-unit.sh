#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-scheduler-runtime-test.$$"
trap 'rm -f "$OUT"' EXIT
HOST_CXX="${HOST_CXX:-g++}"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/scheduler_runtime_test.cpp" \
  "$ROOT/kernel/core/scheduler.cpp" \
  -o "$OUT"
"$OUT"
