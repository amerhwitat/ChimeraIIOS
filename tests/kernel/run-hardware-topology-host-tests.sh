#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="$ROOT/build/koronos/hardware-topology-host"
mkdir -p "$BUILD"
python3 "$ROOT/tools/isa/generate_cpu_arch_registry.py"
"${CXX:-g++}" -std=c++17 -Wall -Wextra -Werror \
  -I"$ROOT/kernel/include" -I"$ROOT/kernel/generated" \
  "$ROOT/kernel/core/hardware.cpp" \
  "$ROOT/kernel/core/cpu_arch_registry.cpp" \
  "$ROOT/tests/kernel/hardware_topology_host_test.cpp" \
  -o "$BUILD/hardware-topology-host-test"
"$BUILD/hardware-topology-host-test"
echo "Koronos CPUID topology host tests passed."
