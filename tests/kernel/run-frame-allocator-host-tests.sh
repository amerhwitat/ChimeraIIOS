#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-frame-allocator-test.$$"
trap 'rm -f "$OUT"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/frame_allocator_test.cpp" \
  "$ROOT/kernel/core/frame_allocator.cpp" \
  -o "$OUT"
"$OUT"
"$OUT" above4g

OUT_PHYSMAP="${TMPDIR:-/tmp}/koronos-physmap-test.$$"
trap 'rm -f "$OUT" "$OUT_PHYSMAP"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/physmap_range_test.cpp" \
  "$ROOT/kernel/core/physmap.cpp" \
  -o "$OUT_PHYSMAP"
"$OUT_PHYSMAP"

OUT_ELF="${TMPDIR:-/tmp}/koronos-elf-loader-test.$$"
trap 'rm -f "$OUT" "$OUT_PHYSMAP" "$OUT_ELF"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/process_loader_transaction_test.cpp" \
  "$ROOT/kernel/core/process_loader.cpp" "$ROOT/kernel/core/elf64.cpp" \
  -o "$OUT_ELF"
"$OUT_ELF"

OUT_ELF_LEGACY="${TMPDIR:-/tmp}/koronos-elf-loader-legacy-test.$$"
trap 'rm -f "$OUT" "$OUT_PHYSMAP" "$OUT_ELF" "$OUT_ELF_LEGACY"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/tests/process_loader_test.cpp" \
  "$ROOT/kernel/core/process_loader.cpp" "$ROOT/kernel/core/elf64.cpp" \
  -o "$OUT_ELF_LEGACY"
"$OUT_ELF_LEGACY"
