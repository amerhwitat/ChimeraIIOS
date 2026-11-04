#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-x86_64-cpu-state-test.$$"
trap 'rm -f "$OUT"' EXIT
"${HOST_CXX:-g++}" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/tests/x86_64_cpu_state_test.cpp" -o "$OUT"
"$OUT"
