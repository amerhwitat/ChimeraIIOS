#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
CXX="${CXX:-g++}"
"$CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/arch_init.cpp" "$ROOT/tests/kernel/cpu_profile_host_test.cpp" \
  -o "$TMP/cpu-profile-host-test"
"$TMP/cpu-profile-host-test"
