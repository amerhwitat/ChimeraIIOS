#!/usr/bin/env bash
set -euo pipefail
cfg="\${1:?usage: test-grub-targets.sh <grub.cfg>}"
for target in "Live desktop" "Installer" "Koronos" "Recovery"; do
  grep -Fq "$target" "$cfg" || { echo "Missing GRUB target: $target" >&2; exit 1; }
done
grep -Fq 'set gfxpayload=keep' "$cfg"
grep -Fq '1920x1080' "$cfg"
grep -Fq '1024x768' "$cfg"
grep -Fq 'loglevel=7' "$cfg"
grep -Fq 'ignore_loglevel' "$cfg"
grep -Fq 'systemd.show_status=1' "$cfg"
grep -Fq 'rd.systemd.show_status=1' "$cfg"
grep -Fq 'chimera.mode=installer' "$cfg"
grep -Fq 'chimera.mode=recovery' "$cfg"
grep -Fq 'multiboot2 /boot/koronos.elf' "$cfg"
echo "GRUB target, verbose boot, and high-resolution framebuffer policy: PASS"
