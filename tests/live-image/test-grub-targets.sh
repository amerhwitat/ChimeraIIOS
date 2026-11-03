#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 5 ]]; then
  echo "usage: $0 <grub.cfg> <spitfire-menu.cfg> <gates-menu.cfg> <jasper-live.cfg> <native-runtime-candidates.json>" >&2
  exit 2
fi
root_cfg="$1"
spitfire_cfg="$2"
gates_cfg="$3"
jasper_cfg="$4"
candidate_manifest="$5"\nboot_contract="$6"

grep -Fq 'configfile /boot/spitfire/spitfire-menu.cfg' "$root_cfg"
grep -Fq 'configfile /boot/gates/gates-menu.cfg' "$spitfire_cfg"
grep -Fq 'Gates — Continue to Jasper / GRUB 2 target manager' "$gates_cfg"
grep -Fq 'configfile /boot/jasper/live-image.cfg' "$gates_cfg"
grep -Fq 'Gates — Boot diagnostics' "$gates_cfg"
grep -Fq 'background_image --mode stretch /boot/grub/background.jpg' "$spitfire_cfg"
grep -Fq 'background_image --mode stretch /boot/grub/background.jpg' "$gates_cfg"
grep -Fq 'background_image --mode stretch /boot/grub/background.jpg' "$jasper_cfg"
for target in "Live — Aurora Desktop" "Live — Safe Graphics" "Linux Rescue Shell" "Native Koronos Installer" "Native Koronos Recovery" "Native kernel diagnostics" "Classic X / Openbox" "UEFI firmware setup" "GRUB 2 command line" "Reboot" "Power off"; do
  grep -Fq "$target" "$jasper_cfg" || { echo "Missing Jasper target: $target" >&2; exit 1; }
done
for cfg in "$root_cfg" "$spitfire_cfg" "$gates_cfg" "$jasper_cfg"; do
  grep -Fq 'set gfxpayload=keep' "$cfg"
done
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

python3 - "$candidate_manifest" "$boot_contract" <<'PY'
import json, pathlib, sys
m = json.loads(pathlib.Path(sys.argv[1]).read_text())
contract = json.loads(pathlib.Path(sys.argv[2]).read_text())
assert contract["primary_loader"] == "GRUB2 BIOS/UEFI El Torito"
assert contract["firmware_menu"] == "Spit Fire"
assert contract["policy_menu"] == "Gates"
assert contract["menu_manager"] == "Jasper"
assert contract["linux_vmlinuz"] is True
assert "/boot/gates/gates-menu.cfg" in contract["spitfire_artifacts"]["menu"]
assert "/boot/jasper/live-image.cfg" in contract["spitfire_artifacts"]["menu"]
assert contract["runtime_candidates"]["installer"].endswith("bootable_by_koronos=false")
assert contract["runtime_candidates"]["recovery"].endswith("bootable_by_koronos=false")
assert m["schema"] == "koronos-native-runtime-candidates-v1"
assert m["status"] == "prototype-built-not-native-koronos-runtime"
for target in ("installer", "recovery"):
    assert m[target]["bootable_by_koronos"] is False
    assert "prototype" in m[target]["runtime_type"].lower()
    assert m[target]["artifacts"], f"{target} candidate artifacts were not built"
    assert all(x["size"] > 0 and len(x["sha256"]) == 64 for x in m[target]["artifacts"])
print("Spit Fire -> Gates -> Jasper routing, native runtime refusal gates and separate Linux rescue: PASS")
PY
