#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD="$ROOT/build-chimera-iso.sh"

bash -n "$BUILD"
bash -n "$ROOT/tools/branding/stage-aurora-image.sh"
bash -n "$ROOT/tools/branding/chimera-set-desktop-background.sh"

grep -q 'FAILED_STAGE_FILE=' "$BUILD"
grep -q 'trap build_failure_trap EXIT' "$BUILD"
grep -q 'automatic resume enabled' "$BUILD"
grep -q 'run_checkpointed_stage' "$BUILD"
grep -q -- '-J -R -V "CHIMERA_II_OS"' "$BUILD"

for f in   "$ROOT/boot/iso/grub.cfg"   "$ROOT/boot/installation/menu.cfg"   "$ROOT/boot/jasper/jasper.cfg"   "$ROOT/boot/jasper/diagnostics.cfg"   "$ROOT/boot/jasper/install.cfg"   "$ROOT/boot/jasper/live.cfg"   "$ROOT/boot/jasper/recovery.cfg"   "$ROOT/boot/spitfire/spitfire-menu.cfg"; do
  grep -q 'background_image' "$f" || {
    echo "FAIL: missing Aurora background in $f"
    exit 1
  }
done

grep -q 'desktop-background.conf' "$ROOT/desktop/aurora/gates_menu.json"
grep -q 'changeable' "$ROOT/desktop/aurora/gates_menu.json"
test -s "$ROOT/system/branding/aurora-default.png.base64"

echo "PASS: Chimera ISO resumability, xorriso flags, and Aurora menu background contracts"
