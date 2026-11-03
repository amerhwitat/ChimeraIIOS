#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "usage: $0 <grub.cfg> <spitfire-menu.cfg> <jasper-live.cfg> [native-runtime-candidates.json]" >&2
  exit 2
fi
root_cfg="$1"
spitfire_cfg="$2"
jasper_cfg="$3"
grep -Fq 'configfile /boot/spitfire/spitfire-menu.cfg' "$root_cfg"
grep -Fq 'configfile /boot/jasper/live-image.cfg' "$spitfire_cfg"
for target in "Live — Aurora Desktop" "Safe Graphics" "Linux Rescue Shell" "Native Koronos Installer" "Native Koronos Recovery" "Native kernel diagnostics" "Classic X / Openbox" "UEFI firmware setup" "GRUB 2 command line" "Reboot" "Power off"; do
  grep -Fq "$target" "$jasper_cfg" || { echo "Missing Jasper target: $target" >&2; exit 1; }
done
grep -Fq 'set gfxpayload=keep' "$root_cfg"
grep -Fq 'set gfxpayload=keep' "$spitfire_cfg"
grep -Fq 'set gfxpayload=keep' "$jasper_cfg"
grep -Fq '5120x2880' "$jasper_cfg"
grep -Fq '1024x768' "$jasper_cfg"
grep -Fq '640x480' "$jasper_cfg"
grep -Fq 'loglevel=7' "$jasper_cfg"
grep -Fq 'ignore_loglevel' "$jasper_cfg"
grep -Fq 'systemd.show_status=1' "$jasper_cfg"
grep -Fq 'multiboot2 /boot/koronos.elf' "$jasper_cfg"
grep -Fq 'insmod multiboot2' "$jasper_cfg"
grep -Fq '/boot/installer/installer-initrd.img' "$jasper_cfg"
grep -Fq '/boot/recovery/chimera-recovery-initramfs.img' "$jasper_cfg"
grep -Fq 'Native Koronos Installer runtime incomplete' "$jasper_cfg"
grep -Fq 'Native Koronos Recovery runtime incomplete' "$jasper_cfg"
! grep -Eq '^[[:space:]]*linux .* quiet([[:space:]]|$)' "$jasper_cfg"
if [[ $# -eq 4 ]]; then
  python3 - "$4" <<'PY'
import json, pathlib, sys
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
assert m["status"] == "prototype-built-not-native-koronos-runtime"
assert m["installer"]["bootable_by_koronos"] is False
assert m["recovery"]["bootable_by_koronos"] is False
PY
fi
echo "Spit Fire -> Jasper/GRUB2 configfile chain, target routing, fail-closed native handoffs and verbose framebuffer policy: PASS"
