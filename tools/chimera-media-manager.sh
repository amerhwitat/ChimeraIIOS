#!/usr/bin/env bash
# Safe removable-media discovery for the Linux live editions.
# Optical media is always mounted read-only. Writable filesystems are mounted
# only from removable/USB devices and only from the explicit allow-list below.
set -Eeuo pipefail

MEDIA_ROOT="${CHIMERA_MEDIA_ROOT:-/media}"
LOG_TAG="chimera-media"
readonly OPTICAL_FS="iso9660 udf"
readonly WRITABLE_FS="ext2 ext3 ext4 xfs btrfs vfat fat fat32 exfat ntfs ntfs3"

log(){ printf '[%s] %s\n' "$LOG_TAG" "$*" >&2; }
need_root(){ [[ "$(id -u)" -eq 0 ]] || { log "must run as root"; exit 77; }; }
safe_name(){
  local value="${1:-media}"
  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+|-+$//g')"
  [[ -n "$value" ]] || value=media
  printf '%s' "$value"
}
is_one_of(){ local wanted="$1" item; shift; for item in "$@"; do [[ "$wanted" == "$item" ]] && return 0; done; return 1; }
mount_device(){
  local dev="$1" type="$2" label="${3:-}" kind="${4:-removable}" name target opts
  [[ -b "$dev" ]] || return 0
  if findmnt -rn -S "$dev" >/dev/null 2>&1; then return 0; fi
  name="$(safe_name "${label:-$(basename "$dev")}")"
  target="$MEDIA_ROOT/$name"
  if mountpoint -q "$target"; then target="$MEDIA_ROOT/$name-$(safe_name "$(basename "$dev")")"; fi
  mkdir -p "$target"
  if [[ "$kind" == optical ]]; then
    is_one_of "$type" $OPTICAL_FS || { rmdir "$target" 2>/dev/null || true; return 0; }
    opts="ro,nosuid,nodev,noexec"
  else
    is_one_of "$type" $WRITABLE_FS || { rmdir "$target" 2>/dev/null || true; log "unsupported removable filesystem $type on $dev (not mounted)"; return 0; }
    opts="rw,nosuid,nodev,noexec"
  fi
  if mount -t "$type" -o "$opts" "$dev" "$target"; then
    log "mounted $dev ($type) at $target ($opts)"
  else
    rmdir "$target" 2>/dev/null || true
    log "mount failed for $dev ($type)"
    return 1
  fi
}
scan(){
  mkdir -p "$MEDIA_ROOT"
  command -v lsblk >/dev/null || { log "lsblk is required"; return 1; }
  while read -r dev kind removable fstype label tran; do
    [[ -b "$dev" ]] || continue
    if [[ "$kind" == rom ]]; then
      fstype="${fstype:-$(blkid -o value -s TYPE "$dev" 2>/dev/null || true)}"
      [[ -n "$fstype" ]] || continue
      mount_device "$dev" "$fstype" "${label:-optical-$(basename "$dev")}" optical || true
    elif [[ "$kind" == part && ( "$removable" == 1 || "$tran" == usb ) ]]; then
      fstype="${fstype:-$(blkid -o value -s TYPE "$dev" 2>/dev/null || true)}"
      [[ -n "$fstype" ]] || continue
      mount_device "$dev" "$fstype" "${label:-$(basename "$dev")}" removable || true
    fi
  done < <(lsblk -pnro NAME,TYPE,RM,FSTYPE,LABEL,TRAN 2>/dev/null || true)
}
mount_iso(){
  local file="$1" name loop target
  [[ -f "$file" && -r "$file" ]] || { log "ISO file is not readable: $file"; return 2; }
  command -v losetup >/dev/null || { log "losetup is required"; return 1; }
  name="$(safe_name "$(basename "$file")")"
  name="${name%.*}"
  target="$MEDIA_ROOT/iso-$name"
  [[ ! -e "$target" ]] || { log "mount target already exists: $target"; return 1; }
  mkdir -p "$target"
  loop="$(losetup --find --show --read-only "$file")"
  if ! mount -o ro,nosuid,nodev,noexec "$loop" "$target"; then
    losetup -d "$loop" || true; rmdir "$target" || true; return 1
  fi
  printf '%s\n' "$loop" > "$target/.chimera-loop-device"
  log "mounted ISO $file at $target read-only"
}
unmount_target(){
  local target="$1" loopfile
  mountpoint -q "$target" || { log "not a mountpoint: $target"; return 1; }
  loopfile="$target/.chimera-loop-device"
  umount "$target"
  if [[ -f "$loopfile" ]]; then local loop; loop="$(cat "$loopfile")"; rm -f "$loopfile"; losetup -d "$loop" || true; fi
  rmdir "$target" 2>/dev/null || true
  log "unmounted $target"
}
usage(){ echo "Usage: chimera-media-manager.sh --scan | --mount-iso FILE | --unmount /media/MOUNT"; }
need_root
case "${1:---scan}" in
  --scan) scan ;;
  --mount-iso) [[ -n "${2:-}" ]] || { usage; exit 2; }; mount_iso "$2" ;;
  --unmount) [[ -n "${2:-}" ]] || { usage; exit 2; }; unmount_target "$2" ;;
  *) usage; exit 2 ;;
esac
