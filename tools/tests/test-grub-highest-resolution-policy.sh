#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE='5120x2880,4096x2160,3840x2160,3440x1440,3200x1800,2880x1800,2560x1600,2560x1440,2560x1080,2048x1536,1920x1200,1920x1080,1680x1050,1600x1200,1440x900,1366x768,1280x1024,1280x800,1280x720,1152x864,1024x768,800x600,640x480,auto'
if [[ "$ROOT" == *"OctavianOS"* ]]; then
  targets=(boot/iso/grub.cfg boot/jasper/jasper.cfg boot/jasper/live.cfg boot/jasper/install.cfg boot/jasper/recovery.cfg boot/jasper/safe.cfg boot/jasper/diagnostics.cfg boot/spitfire/spitfire-menu.cfg)
else
  targets=(boot/iso/grub.cfg boot/jasper/jasper.cfg boot/jasper/live.cfg boot/jasper/install.cfg boot/jasper/recovery.cfg boot/jasper/safe-mode.cfg boot/jasper/diagnostics.cfg boot/spitfire/spitfire-menu.cfg)
fi
failed=0
for rel in "${targets[@]}"; do
  file="$ROOT/$rel"
  if [[ ! -f "$file" ]]; then echo "FAIL missing target config: $rel"; failed=1; continue; fi
  if ! grep -Fqx "set gfxmode=$MODE" "$file"; then echo "FAIL highest-mode policy missing/mismatched: $rel"; failed=1; fi
  if ! grep -Fqx 'set gfxpayload=keep' "$file"; then echo "FAIL framebuffer handoff not preserved: $rel"; failed=1; fi
  for fallback in 1024x768 800x600 640x480; do
    if ! grep -F "set gfxmode=$MODE" "$file" | grep -Fq "$fallback"; then echo "FAIL fallback $fallback missing: $rel"; failed=1; fi
  done
done
if (( failed )); then exit 1; fi
echo "PASS: all boot target menus prefer highest advertised GOP/VBE mode and preserve framebuffer handoff."
