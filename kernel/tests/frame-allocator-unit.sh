#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
"${HOST_CXX:-g++}" -std=c++17 -Wall -Wextra -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/frame_allocator.cpp" \
  "$ROOT/kernel/tests/frame_allocator_test.cpp" \
  -o "$TMP/frame-allocator-test"
"$TMP/frame-allocator-test"
