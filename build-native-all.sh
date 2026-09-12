#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${1:-Release}"
"$ROOT/cpp/build-gcc.sh" "$CONFIG"
if [[ -x "$ROOT/ISO-Tool/build-gcc.sh" ]]; then "$ROOT/ISO-Tool/build-gcc.sh" "$CONFIG"; fi
"$ROOT/Flash-Tool/build.sh" "$CONFIG"
printf '[CHIMERA][DONE] Native OS + ISO-Tool + Flash-Tool build sequence complete.\n'
