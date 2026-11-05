#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/tests/process_address_space_test.cpp" \
  "$ROOT/kernel/core/process.cpp" \
  -o "$OUT"
"$OUT"
