#!/usr/bin/env bash
set -Eeuo pipefail
usage(){
cat <<'EOF'
Chimera optical media helper
Usage:
  chimera-media-mount.sh list
  chimera-media-mount.sh mount-iso IMAGE [MOUNTPOINT]
  chimera-media-mount.sh mount-optical [DEVICE] [MOUNTPOINT]
  chimera-media-mount.sh unmount MOUNTPOINT
  chimera-media-mount.sh eject [DEVICE]
Mounts are read-only,nodev,nosuid,noexec and restricted to /mnt/chimera/media.
EOF
}
die(){ echo "[ERROR] $*" >&2; exit 2; }
root(){ (( EUID==0 )) || die "Requires root; use sudo."; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"; }
safe_target(){
  local resolved
  resolved="$(realpath -m -- "$1")"
  [[ "$resolved" == /mnt/chimera/media/* ]] || die "Mountpoint must resolve below /mnt/chimera/media."
  printf "%s" "$resolved"
}
default_target(){ local n="$1"; n="${n##*/}"; n="${n//[^A-Za-z0-9._-]/_}"; printf '/mnt/chimera/media/%s' "$n"; }
list_media(){
  if command -v lsblk >/dev/null 2>&1; then
    lsblk -o NAME,TYPE,FSTYPE,LABEL,SIZE,RO,MOUNTPOINTS
  fi
  if command -v findmnt >/dev/null 2>&1; then
    echo "== Chimera media mounts =="
    findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS | grep -F '/mnt/chimera/media/' || true
  fi
}
mount_iso(){
  root; need mount; need file
  local image="$1" target="${2:-}"
  [[ -f "$image" && -r "$image" ]] || die "Unreadable ISO file: $image"
  [[ -n "$target" ]] || target="$(default_target "$image")"; target="$(safe_target "$target")"
  mkdir -p "$target"; mountpoint -q "$target" && die "Already mounted: $target"
  local kind; kind="$(file -b "$image")"
  [[ "$kind" == *"ISO 9660"* || "$kind" == *"UDF"* || "$kind" == *"DVD"* || "$kind" == *"CD-ROM"* ]] || die "Not recognized as ISO-9660/UDF media: $kind"
  mount -o loop,ro,nodev,nosuid,noexec "$image" "$target"
  echo "[SUCCESS] Mounted read-only: $image -> $target"
}
mount_optical(){
  root; need mount; need blkid
  local dev="${1:-/dev/sr0}" target="${2:-}"
  [[ -b "$dev" ]] || die "Optical device not found: $dev"
  [[ -n "$target" ]] || target="$(default_target "$dev")"; target="$(safe_target "$target")"
  local fs; fs="$(blkid -o value -s TYPE "$dev" 2>/dev/null || true)"
  [[ "$fs" == iso9660 || "$fs" == udf ]] || die "Unsupported/unreadable optical filesystem: ${fs:-unknown}"
  mkdir -p "$target"; mountpoint -q "$target" && die "Already mounted: $target"
  mount -t "$fs" -o ro,nodev,nosuid,noexec "$dev" "$target"
  echo "[SUCCESS] Mounted $dev -> $target ($fs)"
}
unmount_media(){ root; need umount; local target; target="$(safe_target "$1")"; mountpoint -q "$target" || die "Not mounted: $target"; umount -- "$target"; rmdir "$target" 2>/dev/null || true; }
eject_media(){ root; need eject; local dev="${1:-/dev/sr0}"; [[ -b "$dev" ]] || die "Device not found: $dev"; eject "$dev"; }
main(){
 (($#)) || { usage; return 0; }; local cmd="$1"; shift
 case "$cmd" in
  -h|--help|help) usage;;
  list) (($#==0)) || die "list takes no args"; list_media;;
  mount-iso) (($#>=1 && $#<=2)) || die "mount-iso IMAGE [MOUNTPOINT]"; mount_iso "$@";;
  mount-optical) (($#<=2)) || die "mount-optical [DEVICE] [MOUNTPOINT]"; mount_optical "$@";;
  unmount) (($#==1)) || die "unmount MOUNTPOINT"; unmount_media "$1";;
  eject) (($#<=1)) || die "eject [DEVICE]"; eject_media "$@";;
  *) die "Unknown command: $cmd (use --help)";;
 esac
}
main "$@"
