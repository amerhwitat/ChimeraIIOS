#!/usr/bin/env bash
set -euo pipefail
root=${1:-/}
[[ $EUID -eq 0 ]] || { echo "Run as root to prepare a target root tree." >&2; exit 2; }
[[ -d "$root" ]] || { echo "Target root does not exist: $root" >&2; exit 2; }
for d in boot/efi system/chimera etc/chimera var/log var/lib/chimera var/cache var/spool run/chimera run/services run/devices dev proc sys home root srv opt/chimera lib lib64 mnt media tmp usr/bin usr/sbin usr/lib usr/lib64 usr/include usr/share; do
  install -d -m 0755 "$root/$d"
done
chmod 1777 "$root/tmp"
for name in bin sbin lib lib64; do
  [[ -e "$root/$name" || -L "$root/$name" ]] && continue
  [[ -d "$root/usr/$name" ]] && ln -s "usr/$name" "$root/$name"
done
