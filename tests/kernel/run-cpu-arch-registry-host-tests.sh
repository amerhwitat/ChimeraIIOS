#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="$ROOT/build/koronos/cpu-arch-registry-host"
mkdir -p "$BUILD"
python3 "$ROOT/tools/isa/generate_cpu_arch_registry.py"
"${CXX:-g++}" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" -I"$ROOT/kernel/generated" \
  "$ROOT/kernel/core/cpu_arch_registry.cpp" "$ROOT/tests/kernel/cpu_arch_registry_host_test.cpp" \
  -o "$BUILD/cpu-arch-registry-host-test"
"$BUILD/cpu-arch-registry-host-test"
echo "Koronos CPU architecture registry tests: PASS"
