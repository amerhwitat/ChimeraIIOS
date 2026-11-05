#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="${TMPDIR:-/tmp}/chimera-qfs-probe-host-test"
mkdir -p "$BUILD"
"${CXX:-g++}" -std=c++20 -Wall -Wextra -Wpedantic \
  -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/block_device.cpp" \
  "$ROOT/kernel/core/qfs_probe.cpp" \
  "$ROOT/tests/kernel/qfs_probe_test.cpp" \
  -o "$BUILD/qfs-probe-test"
"$BUILD/qfs-probe-test"
echo "PASS: QFS v1 superblock probe and geometry validation"
