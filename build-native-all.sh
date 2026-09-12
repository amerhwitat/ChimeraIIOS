#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-Release}"
"$ROOT/cpp/build-gcc.sh" "$CONFIG"
if [[ -x "$ROOT/build/$CONFIG/chimera_native_tools" ]]; then
  "$ROOT/build/$CONFIG/chimera_native_tools" "$ROOT"
elif [[ -x "$ROOT/build/chimera_native_tools" ]]; then
  "$ROOT/build/chimera_native_tools" "$ROOT"
fi
if [[ -x "$ROOT/ISO-Tool/build-gcc.sh" ]]; then "$ROOT/ISO-Tool/build-gcc.sh" "$CONFIG"; fi
"$ROOT/Flash-Tool/build.sh" "$CONFIG"
printf '[CHIMERA][DONE] Native ASM/C/C++ OS + native validators + ISO-Tool + Flash-Tool build sequence complete.\n'
