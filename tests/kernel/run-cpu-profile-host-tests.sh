#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
HOST_CXX="${HOST_CXX:-g++}"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/arch_init.cpp" "$ROOT/kernel/core/arch_backend.cpp" "$ROOT/tests/kernel/cpu_profile_host_test.cpp" \
  -o "$TMP/cpu-profile-host-test"
"$TMP/cpu-profile-host-test"
