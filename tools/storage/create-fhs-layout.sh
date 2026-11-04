#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 1 ]] || { echo "Usage: create-fhs-layout.sh TARGET_ROOT" >&2; exit 2; }
root=$1
[[ $EUID -eq 0 ]] || { echo "Run as root to prepare a target root tree." >&2; exit 2; }
[[ -d "$root" && "$root" != "/" ]] || { echo "Target root must be an existing staging directory, never /." >&2; exit 2; }
for d in boot/efi system/chimera etc/chimera etc/samba var/log var/lib/chimera var/cache var/spool var/tmp var/opt run/chimera run/services run/devices run/lock run/user dev/pts dev/shm proc sys home root srv opt/chimera mnt media tmp usr/bin usr/sbin usr/lib usr/lib64 usr/local/bin usr/local/sbin usr/local/etc usr/local/include usr/local/lib usr/local/share usr/include usr/share usr/share/applications; do
  install -d -m 0755 "$root/$d"
done
chmod 1777 "$root/tmp" "$root/var/tmp"
chmod 0700 "$root/root"
for name in bin sbin lib lib64; do
  [[ -e "$root/$name" || -L "$root/$name" ]] && continue
  [[ -d "$root/usr/$name" ]] && ln -s "usr/$name" "$root/$name"
done
