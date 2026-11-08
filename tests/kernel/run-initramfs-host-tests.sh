#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-g++}"
"$CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/initramfs.cpp" "$ROOT/tests/kernel/test_initramfs.cpp" \
  -o "$TMP/test-initramfs"
"$TMP/test-initramfs"
