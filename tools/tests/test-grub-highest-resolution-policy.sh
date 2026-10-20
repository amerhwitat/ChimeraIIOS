#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE='5120x2880x32,5120x2880x24,5120x2880,4096x2160x32,4096x2160x24,4096x2160,3840x2160x32,3840x2160x24,3840x2160,3440x1440x32,3440x1440x24,3440x1440,3200x1800x32,3200x1800x24,3200x1800,2880x1800x32,2880x1800x24,2880x1800,2560x1600x32,2560x1600x24,2560x1600,2560x1440x32,2560x1440x24,2560x1440,2560x1080x32,2560x1080x24,2560x1080,2048x1536x32,2048x1536x24,2048x1536,1920x1200x32,1920x1200x24,1920x1200,1920x1080x32,1920x1080x24,1920x1080,1680x1050x32,1680x1050x24,1680x1050,1600x1200x32,1600x1200x24,1600x1200,1600x900x32,1600x900x24,1600x900,1440x900x32,1440x900x24,1440x900,1366x768x32,1366x768x24,1366x768,1280x1024x32,1280x1024x24,1280x1024,1280x800x32,1280x800x24,1280x800,1280x720x32,1280x720x24,1280x720,1152x864x32,1152x864x24,1152x864,1024x768x32,1024x768x24,1024x768,800x600x32,800x600x24,800x600,640x480x32,640x480x24,640x480,auto'
failed=0
check_tree() {
  local tree="$1"
  [[ -d "$tree/boot" ]] || return 0
  local safe="boot/jasper/safe-mode.cfg"
  [[ -f "$tree/boot/jasper/safe.cfg" ]] && safe="boot/jasper/safe.cfg"
  local targets=(boot/iso/grub.cfg boot/jasper/jasper.cfg boot/jasper/live.cfg boot/jasper/install.cfg boot/jasper/recovery.cfg "$safe" boot/jasper/diagnostics.cfg boot/spitfire/spitfire-menu.cfg boot/installation/menu.cfg)
  for rel in "${targets[@]}"; do
    local file="$tree/$rel"
    if [[ ! -f "$file" ]]; then echo "FAIL missing target config: $file"; failed=1; continue; fi
    if ! grep -Fqx "set gfxmode=$MODE" "$file"; then echo "FAIL highest-mode/depth ladder missing or mismatched: $file"; failed=1; fi
    if ! grep -Fqx 'set gfxpayload=keep' "$file"; then echo "FAIL framebuffer handoff not preserved: $file"; failed=1; fi
    for fallback in 1024x768 800x600 640x480; do
      if ! grep -F "set gfxmode=$MODE" "$file" | grep -Fq "$fallback"; then echo "FAIL fallback $fallback missing: $file"; failed=1; fi
    done
  done
}
check_tree "$ROOT"
check_tree "$ROOT/vendor/chimera-ii-os/source"
if (( failed )); then exit 1; fi
echo "PASS: target menus prefer highest advertised GOP/VBE mode and color depth, with safe fallbacks and framebuffer preservation."
