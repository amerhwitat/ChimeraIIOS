#!/bin/sh
# Discover an existing Chimera/Linux-compatible installation without making it
# the boot root. Live and Recovery always retain their self-contained initramfs
# root; discovered disks are mounted read-only for inspection/repair.
set -eu

MODE=${1:-live}
MOUNTPOINT=${CHIMERA_INSTALLED_ROOT_MOUNT:-/mnt/chimera-installed}
STATE_DIR=${CHIMERA_ROOT_STATE_DIR:-/run/chimera}
STATE_FILE="$STATE_DIR/installed-root.state"
mkdir -p "$MOUNTPOINT" "$STATE_DIR"
: > "$STATE_FILE"

log() {
  printf '[ROOT-DISCOVERY] %s\n' "$*" > /dev/console 2>/dev/null || printf '[ROOT-DISCOVERY] %s\n' "$*"
}
record() {
  printf '%s=%s\n' "$1" "$2" >> "$STATE_FILE"
}

record mode "$MODE"
record runtime_root "initramfs"
record persistence "no"
record installed_root "none"

# Never assume that a block node is a system root. Exclude optical media and
# whole-disk nodes; inspect partitions only. A candidate must have a supported
# filesystem, mount read-only, and contain an OS identity marker.
for dev in /dev/nvme*n*p* /dev/mmcblk*p* /dev/vd[a-z][0-9]* /dev/sd[a-z][0-9]*; do
  [ -b "$dev" ] || continue
  [ -x /bin/blkid ] || continue

  fstype="$(blkid -o value -s TYPE "$dev" 2>/dev/null || true)"
  case "$fstype" in
    ext2|ext3|ext4|xfs|btrfs|vfat|exfat|ntfs) ;;
    *) continue ;;
  esac

  # Use a fresh private mountpoint per candidate. No candidate is ever mounted
  # read-write by this discovery helper.
  candidate="$MOUNTPOINT"
  if mount -o ro "$dev" "$candidate" 2>/dev/null; then
    identity=""
    if [ -s "$candidate/etc/os-release" ]; then
      identity="os-release"
    elif [ -s "$candidate/etc/koronos-release" ]; then
      identity="koronos-release"
    elif [ -s "$candidate/boot/koronos/root-manifest.json" ]; then
      identity="koronos-manifest"
    fi

    if [ -n "$identity" ]; then
      record installed_root "$dev"
      record filesystem "$fstype"
      record identity "$identity"
      record mountpoint "$candidate"
      record mount_mode "ro"
      log "validated installed root: device=$dev fs=$fstype identity=$identity mode=ro"
      exit 0
    fi

    umount "$candidate" 2>/dev/null || true
  fi
done

record fallback "no-validated-installed-root"
log "no validated installed root found; retaining self-contained RAM initramfs root"
exit 0
