#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-g++}"
"$CXX" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/framebuffer.cpp" "$ROOT/kernel/tests/framebuffer_test.cpp" -o "$TMP/framebuffer-test"
"$TMP/framebuffer-test"
