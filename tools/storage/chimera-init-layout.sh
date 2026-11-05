#!/usr/bin/env bash
set -Eeuo pipefail
usage(){ echo "Usage: chimera-init-layout.sh [--root TARGET_ROOT]"; echo "Creates FHS directories; does not mount pseudo-filesystems."; }
root=/
while (($#)); do
 case "$1" in
  --root) (($#>=2)) || { usage >&2; exit 2; }; root="$2"; shift 2;;
  -h|--help) usage; exit 0;;
  *) echo "Unknown option: $1" >&2; usage >&2; exit 2;;
 esac
done
[[ "$root" == /* ]] || { echo "[ERROR] TARGET_ROOT must be absolute." >&2; exit 2; }
mkdir -p "$root"; root="$(realpath -m "$root")"
for path in \
 boot/efi system/chimera/kernel/modules usr/bin usr/sbin usr/lib usr/lib64 usr/include usr/share \
 etc/chimera/{installer,hardware,drivers,network,storage,aurora,services,identity} etc/fstab.d \
 var/log var/lib/chimera var/lib/chimera/network var/lib/chimera/media var/cache var/spool \
 run/chimera run/services run/devices dev proc sys home root srv/{smb,nfs,web,chimera-node} \
 opt/chimera/{aurora,drivers,research} lib lib64 mnt media tmp mnt/chimera/media mnt/chimera/network
do install -d -m 0755 "$root/$path"; done
chmod 1777 "$root/tmp"
chmod 0700 "$root/root" 2>/dev/null || true
echo "[SUCCESS] Linux/Chimera hierarchy created under $root"
echo "[INFO] /proc, /sys and /dev are mountpoints; mount their kernel filesystems at boot."
