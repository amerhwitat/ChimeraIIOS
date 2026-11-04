#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
g++ -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/hardware.cpp" "$ROOT/tests/kernel/hardware_topology_host_test.cpp" \
  -o "$TMP/hardware-topology-host-test"
"$TMP/hardware-topology-host-test"
echo "Koronos CPUID topology host tests passed."
