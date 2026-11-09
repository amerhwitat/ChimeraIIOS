#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-g++}"
"$CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/service.cpp" "$ROOT/tests/kernel/test_service_manager.cpp" \
  -o "$TMP/test-service-manager"
"$TMP/test-service-manager"
printf 'PASS: Kore service activation, health gating, dependency blocking, and cycle rejection\n'
