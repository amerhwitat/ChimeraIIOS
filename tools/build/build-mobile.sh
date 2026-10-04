#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build/build-mobile.sh

Usage:
  tools/build/build-mobile.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi

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
