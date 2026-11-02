#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-process-runtime-test.$$"
trap 'rm -f "$OUT"' EXIT
"${HOST_CXX:-g++}" -std=c++20 -Wall -Wextra -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/elf64.cpp" \
  "$ROOT/kernel/core/process_loader.cpp" \
  "$ROOT/kernel/core/process.cpp" \
  "$ROOT/kernel/tests/process_runtime_test.cpp" \
  -o "$OUT"
"$OUT"
