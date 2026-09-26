#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

grep -Eq '^global[[:space:]]+start([[:space:]]|$)' "$ROOT/boot/spitfire/sf1_longmode.asm"
grep -Eq '^ENTRY\(start\)' "$ROOT/boot/spitfire/spitfire.ld"
grep -Eq 'ignore-garbage|tr[[:space:]]+-d.*base64|base64\.b64decode' "$ROOT/tools/branding/stage-aurora-image.sh"
grep -Eq 'PNG|png|aurora-default\.png' "$ROOT/tools/branding/stage-aurora-image.sh"
echo "boot artifact regressions: OK"
