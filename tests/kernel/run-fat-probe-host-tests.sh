#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${TMPDIR:-/tmp}/chimera-fat-probe-host-test"
mkdir -p "$BUILD"
"${CXX:-g++}" -std=c++20 -Wall -Wextra -Wpedantic -I"$ROOT/kernel/include" \
 "$ROOT/kernel/core/block_device.cpp" "$ROOT/kernel/core/fat_probe.cpp" \
 "$ROOT/tests/kernel/fat_probe_test.cpp" -o "$BUILD/fat-probe-test"
"$BUILD/fat-probe-test"
echo "PASS: FAT12/16/32 and exFAT boot-sector probe contracts"
