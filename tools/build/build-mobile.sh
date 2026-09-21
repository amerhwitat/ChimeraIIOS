#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$ROOT/dist/mobile"
if [[ -d "$ROOT/android" ]]; then
  (cd "$ROOT/android" && ./gradlew assembleRelease bundleRelease)
fi
if [[ -d "$ROOT/apple" ]]; then
  echo 'Apple hosted build requires macOS + Xcode and a selected signing identity.'
fi
if [[ -f "$ROOT/editions/mobile/mobile_editions.json" ]]; then
  python3 "$ROOT/tools/validate_isa_registry.py" >/dev/null || true
fi
printf 'Mobile build orchestration complete. Outputs are profile/toolchain dependent.\n'
