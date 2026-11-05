#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${TMPDIR:-/tmp}/chimera-block-device-host-test"
mkdir -p "$BUILD"
"${CXX:-g++}" -std=c++20 -Wall -Wextra -Wpedantic \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/block_device.cpp" \
  "$ROOT/tests/kernel/block_device_test.cpp" \
  -o "$BUILD/block-device-test"
"$BUILD/block-device-test"
echo "PASS: bounded block-device registry and I/O contracts"
