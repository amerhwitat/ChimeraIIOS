#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tests/boot/test-boot-artifact-regressions.sh

Usage:
  tests/boot/test-boot-artifact-regressions.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

grep -Eq '^global[[:space:]]+start([[:space:]]|$)' "$ROOT/boot/spitfire/sf1_longmode.asm"
grep -Eq '^ENTRY\(start\)' "$ROOT/boot/spitfire/spitfire.ld"
grep -Eq 'ignore-garbage|tr[[:space:]]+-d.*base64|base64\.b64decode' "$ROOT/tools/branding/stage-aurora-image.sh"
grep -Eq 'PNG|png|aurora-default\.png' "$ROOT/tools/branding/stage-aurora-image.sh"
echo "boot artifact regressions: OK"
