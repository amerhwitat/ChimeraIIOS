#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
g++ -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/vfs.cpp" "$ROOT/kernel/core/process_fd.cpp" \
  "$ROOT/tests/kernel/process_fd_host_test.cpp" -o "$TMP/process-fd-host-test"
"$TMP/process-fd-host-test"
echo "Koronos process-owned descriptor host tests passed."
