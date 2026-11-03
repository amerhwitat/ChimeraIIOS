#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 4 ]]; then
  echo "usage: $0 <grub.cfg> <spitfire-menu.cfg> <jasper-menu.cfg> <candidate-manifest.json>" >&2
  exit 2
fi
root_cfg="$1"
spitfire_cfg="$2"
jasper_cfg="$3"
candidate_manifest="$4"

grep -Fq 'configfile /boot/spitfire/spitfire-menu.cfg' "$root_cfg"
grep -Fq 'configfile /boot/jasper/live-image.cfg' "$spitfire_cfg"
grep -Fq 'Live — Aurora Desktop (Linux Live)' "$jasper_cfg"
grep -Fq 'Live — Safe Graphics' "$jasper_cfg"
grep -Fq 'Recovery — Linux Rescue Shell (separate Linux runtime)' "$jasper_cfg"
grep -Fq 'Installer — Native Koronos Installer (complete runtime required)' "$jasper_cfg"
grep -Fq 'Recovery — Native Koronos Recovery (complete runtime required)' "$jasper_cfg"
grep -Fq 'Koronos — Native kernel diagnostics (experimental)' "$jasper_cfg"
grep -Fq 'Classic X / Openbox session' "$jasper_cfg"
grep -Fq 'UEFI firmware setup' "$jasper_cfg"
grep -Fq 'GRUB 2 command line' "$jasper_cfg"
grep -Fq 'set gfxpayload=keep' "$jasper_cfg"
grep -Fq '5120x2880' "$jasper_cfg"
grep -Fq '1920x1080' "$jasper_cfg"
grep -Fq '1024x768' "$jasper_cfg"
grep -Fq '640x480' "$jasper_cfg"
grep -Fq 'loglevel=7' "$jasper_cfg"
grep -Fq 'ignore_loglevel' "$jasper_cfg"
grep -Fq 'earlycon=uart,io,0x3f8,115200' "$jasper_cfg"
grep -Fq 'log_buf_len=4M' "$jasper_cfg"
grep -Fq 'systemd.show_status=1' "$jasper_cfg"
grep -Fq 'rd.systemd.show_status=1' "$jasper_cfg"
grep -Fq 'systemd.log_level=debug' "$jasper_cfg"
grep -Fq 'udev.log_level=debug' "$jasper_cfg"
grep -Fq 'chimera.mode=recovery' "$jasper_cfg"
grep -Fq '/boot/candidates/installer/native-installer-runtime.ready' "$jasper_cfg"
grep -Fq '/boot/candidates/recovery/native-recovery-runtime.ready' "$jasper_cfg"
grep -Fq '/boot/candidates/installer/installer-initrd.img' "$jasper_cfg"
grep -Fq '/boot/candidates/installer/installation.img' "$jasper_cfg"
grep -Fq '/boot/candidates/recovery/chimera-recovery-initramfs.img' "$jasper_cfg"
grep -Fq 'multiboot2 /boot/koronos.elf' "$jasper_cfg"
! grep -Eq '^[[:space:]]*linux .* quiet([[:space:]]|$)' "$jasper_cfg"

python3 - "$candidate_manifest" <<'PY'
import json, pathlib, sys
m = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert m["schema"] == "koronos-native-runtime-candidates-v1"
assert m["installer"]["bootable"] is False
assert m["recovery"]["bootable"] is False
assert m["status"] == "built-candidate-not-production-runtime"
for target in ("installer", "recovery"):
    assert m[target]["artifacts"], f"{target} candidate artifacts were not built"
    assert all(x["size"] > 0 and len(x["sha256"]) == 64 for x in m[target]["artifacts"])
print("GRUB routes, fail-closed native-runtime gates, and separate Linux rescue: PASS")
PY
