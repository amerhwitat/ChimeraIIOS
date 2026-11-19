#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-newc-test-$$"
trap 'rm -f "$OUT"' EXIT
"${CXX:-g++}" -std=c++17 -O2 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/initramfs_newc.cpp" \
  "$ROOT/kernel/core/initramfs_fs.cpp" \
  "$ROOT/tests/kernel/initramfs_newc_test.cpp" -o "$OUT"
"$OUT"
