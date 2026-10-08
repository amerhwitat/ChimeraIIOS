#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/tests/test-iso-resume-and-aurora.sh

Usage:
  tools/tests/test-iso-resume-and-aurora.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="$ROOT/build-chimera-iso.sh"

bash -n "$BUILD"
bash -n "$ROOT/tools/branding/stage-aurora-image.sh"
bash -n "$ROOT/tools/branding/chimera-set-desktop-background.sh"

grep -q 'FAILED_FILE=' "$BUILD"
grep -q "trap 'rc=\$?" "$BUILD"
grep -q -- '--resume' "$BUILD"
grep -q 'run_stage(){' "$BUILD"
grep -q 'xorriso -indev' "$BUILD"

for f in   "$ROOT/boot/iso/grub.cfg"   "$ROOT/boot/installation/menu.cfg"   "$ROOT/boot/jasper/jasper.cfg"   "$ROOT/boot/jasper/diagnostics.cfg"   "$ROOT/boot/jasper/install.cfg"   "$ROOT/boot/jasper/live.cfg"   "$ROOT/boot/jasper/recovery.cfg"   "$ROOT/boot/spitfire/spitfire-menu.cfg"; do
  grep -q 'background_image' "$f" || {
    echo "FAIL: missing Aurora background in $f"
    exit 1
  }
done

grep -q 'desktop-background.conf' "$ROOT/desktop/aurora/gates_menu.json"
grep -q 'changeable' "$ROOT/desktop/aurora/gates_menu.json"
test -s "$ROOT/boot/visual/aurora-wayland-glass.jpg.b64"

echo "PASS: Chimera ISO resume state, failure trap, xorriso verification, and Aurora menu background contracts"
