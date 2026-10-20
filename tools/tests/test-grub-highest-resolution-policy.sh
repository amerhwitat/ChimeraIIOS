#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
    local mode_line
    mode_line="$(grep -m1 '^set gfxmode=' "$file" || true)"
    if [[ -z "$mode_line" ]]; then echo "FAIL gfxmode not configured: $file"; failed=1; continue; fi
    for required in 5120x2880 1024x768 800x600 640x480; do
      if [[ "$mode_line" != *"$required"* ]]; then echo "FAIL mode/fallback $required missing: $file"; failed=1; fi
    done
    if ! grep -Fqx 'set gfxpayload=keep' "$file"; then echo "FAIL framebuffer handoff not preserved: $file"; failed=1; fi
  done
}
check_tree "$ROOT"
check_tree "$ROOT/vendor/chimera-ii-os/source"
if (( failed )); then exit 1; fi
echo "PASS: all target menus declare a highest-resolution-first ladder, standard low-resolution fallbacks, and framebuffer preservation."
