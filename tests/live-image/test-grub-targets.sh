#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 4 || $# -gt 6 ]]; then
  echo "usage: $0 <grub.cfg> <spitfire-menu.cfg> <gates-menu.cfg> <jasper-live.cfg> [native-runtime-candidates.json] [boot-menu-contract.json]" >&2
  exit 2
fi
root_cfg="$1"
spitfire_cfg="$2"
gates_cfg="$3"
jasper_cfg="$4"
grep -Fq 'configfile /boot/spitfire/spitfire-menu.cfg' "$root_cfg"
grep -Fq 'configfile /boot/gates/gates-menu.cfg' "$spitfire_cfg"
grep -Fq 'direct-gates' "$spitfire_cfg"
grep -Fq 'direct-jasper' "$spitfire_cfg"
grep -Fq 'configfile /boot/jasper/live-image.cfg' "$gates_cfg"
for target in "Live — Aurora Desktop" "Safe Graphics" "Linux Rescue Shell" "Native Koronos Installer" "Native Koronos Recovery" "Native kernel diagnostics" "Classic X / Openbox" "UEFI firmware setup" "GRUB 2 command line" "Reboot" "Power off"; do
  grep -Fq "$target" "$jasper_cfg" || { echo "Missing Jasper target: $target" >&2; exit 1; }
done
for cfg in "$root_cfg" "$spitfire_cfg" "$gates_cfg" "$jasper_cfg"; do
  grep -Fq 'set gfxpayload=keep' "$cfg" || { echo "Missing gfxpayload=keep in $cfg" >&2; exit 1; }
done
grep -Fq '5120x2880' "$jasper_cfg"
grep -Fq '1024x768' "$jasper_cfg"
grep -Fq '640x480' "$jasper_cfg"
grep -Fq 'loglevel=7' "$jasper_cfg"
grep -Fq 'ignore_loglevel' "$jasper_cfg"
grep -Fq 'systemd.show_status=1' "$jasper_cfg"
grep -Fq 'multiboot2 /boot/koronos.elf' "$jasper_cfg"
grep -Fq 'native-installer-runtime.ready' "$jasper_cfg"
grep -Fq 'native-recovery-runtime.ready' "$jasper_cfg"
! grep -Eq '^[[:space:]]*linux .* quiet([[:space:]]|$)' "$jasper_cfg"
if [[ $# -ge 5 ]]; then
  python3 - "$5" <<'PY'
import json, pathlib, sys
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
assert m["status"] == "prototype-built-not-native-koronos-runtime"
assert m["installer"]["bootable_by_koronos"] is False
assert m["recovery"]["bootable_by_koronos"] is False
PY
fi
if [[ $# -eq 6 ]]; then
  python3 - "$6" <<'PY'
import json, pathlib, sys
m=json.loads(pathlib.Path(sys.argv[1]).read_text())
assert m["schema"] in {"CHM-BOOT-MENU-5", "CHM-BOOT-MENU-6"}
assert m["policy_menu"] == "Gates"
assert m["menu_manager"] == "Jasper"
assert m["primary_loader"].startswith("GRUB2")
PY
fi
echo "GRUB2 -> Spit Fire -> Gates -> Jasper chain, target routing and fail-closed native handoffs: PASS"
