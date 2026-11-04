#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="$ROOT/build/koronos/apic-topology-host"
mkdir -p "$BUILD"
"${CXX:-g++}" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/apic_topology.cpp" "$ROOT/tests/kernel/apic_topology_host_test.cpp" \
  -o "$BUILD/apic-topology-host-test"
"$BUILD/apic-topology-host-test"
echo "Koronos ACPI MADT topology parser tests: PASS"
