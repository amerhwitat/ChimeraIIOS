#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
HOST_CXX="${HOST_CXX:-g++}"
"$HOST_CXX" -std=c++20 -Wall -Wextra -Werror -I"$ROOT/kernel/include" "$ROOT/kernel/core/registry.cpp" "$ROOT/tests/kernel/registry_host_test.cpp" -o "$TMP/registry-test"
"$TMP/registry-test"
for hive in machine environment kernel; do
  python3 "$ROOT/tools/registry/registry_hive.py" build --input "$ROOT/system/registry/$hive.defaults.json" --output "$TMP/$hive.hive"
  python3 "$ROOT/tools/registry/registry_hive.py" verify "$TMP/$hive.hive"
done
