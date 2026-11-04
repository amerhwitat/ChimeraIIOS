#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-vfs-host-test"
CXX="${CXX:-g++}"
"$CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/vfs.cpp" "$ROOT/tests/kernel/vfs_host_test.cpp" -o "$OUT"
"$OUT"
rm -f "$OUT"
echo "Koronos bounded VFS host tests: PASS"
