#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
"${CXX:-g++}" -std=c++17 -Wall -Wextra -Werror -I"$ROOT/kernel/include" \
  "$ROOT/kernel/core/elf64.cpp" "$ROOT/kernel/core/process.cpp" \
  "$ROOT/kernel/tests/process_admission.cpp" -o "$tmp/process-admission-test"
"$tmp/process-admission-test"
