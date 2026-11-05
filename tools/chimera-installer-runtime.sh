#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-installer-runtime.sh

Usage:
  tools/chimera-installer-runtime.sh [root]

The optional root argument is the filesystem root to inspect (default: /).
This command performs a read-only storage capability preflight. It does not
partition, format, mount, or install to a disk.
CHIMERA_HELP
  exit 0
fi

set -eu
ROOT=${1:-/}
LOG=/var/log/mesgs
PROGRESS=${CHIMERA_PROGRESS_FILE:-$ROOT/run/chimera/progress.state}
mkdir -p "$ROOT$LOG" "$ROOT/var/log/mesgs/archive" "$ROOT/run/chimera"

progress() {
  pct=$1; phase=$2; msg=$3
  printf '%s|%s|%s\n' "$pct" "$phase" "$msg" > "$PROGRESS" 2>/dev/null || true
  printf '[PROGRESS] %s%% | %s | %s\n' "$pct" "$phase" "$msg" >> "$ROOT$LOG/mesgs" 2>/dev/null || true
}
log() {
  printf '%s\n' "$*" >> "$ROOT$LOG/mesgs" 2>/dev/null || true
}
find_tool() {
  name=$1
  for dir in "$ROOT/usr/sbin" "$ROOT/sbin" "$ROOT/usr/bin" "$ROOT/bin"; do
    if [ -x "$dir/$name" ]; then printf '%s\n' "$dir/$name"; return 0; fi
  done
  command -v "$name" 2>/dev/null || return 1
}
has_fs_driver() {
  fs=$1
  [ -r "$ROOT/proc/filesystems" ] || return 1
  awk -v wanted="$fs" '$NF == wanted { found=1 } END { exit !found }' "$ROOT/proc/filesystems"
}
has_block_device() {
  for pattern in sd[a-z] vd[a-z] xvd[a-z] nvme[0-9]n[0-9] mmcblk[0-9] virtio[0-9]; do
    # The glob is intentionally limited to whole-disk device names.
    for device in "$ROOT"/dev/$pattern; do
      [ -b "$device" ] && return 0
    done
  done
  return 1
}

progress 5 'Installer' 'Runtime initialization'
log '[INST] Read-only installer storage preflight started'
progress 20 'Hardware' 'Checking storage inventory and block-device access'

missing=''
for tool in lsblk blkid mount umount; do
  if ! find_tool "$tool" >/dev/null 2>&1; then
    missing="$missing $tool"
  fi
done
if ! find_tool sfdisk >/dev/null 2>&1 && ! find_tool parted >/dev/null 2>&1; then
  missing="$missing sfdisk|parted"
fi

if [ -n "$missing" ]; then
  log "[INST][BLOCKED] Required storage utilities unavailable:$missing"
fi
if ! has_block_device; then
  log '[INST][BLOCKED] No supported whole-disk block device found under /dev'
  missing="$missing block-device"
fi

available=''
# A filesystem is offered only when both its kernel driver is currently
# registered and a matching formatter is present in the live environment.
if has_fs_driver ext4 && find_tool mkfs.ext4 >/dev/null 2>&1; then available="$available ext4"; fi
if has_fs_driver xfs && find_tool mkfs.xfs >/dev/null 2>&1; then available="$available xfs"; fi
if has_fs_driver btrfs && find_tool mkfs.btrfs >/dev/null 2>&1; then available="$available btrfs"; fi
if has_fs_driver vfat && { find_tool mkfs.vfat >/dev/null 2>&1 || find_tool mkfs.fat >/dev/null 2>&1; }; then available="$available vfat"; fi
if has_fs_driver ntfs3 && { find_tool mkfs.ntfs >/dev/null 2>&1 || find_tool mkntfs >/dev/null 2>&1; }; then available="$available ntfs3"; fi
if has_fs_driver exfat && { find_tool mkfs.exfat >/dev/null 2>&1 || find_tool mkexfatfs >/dev/null 2>&1; }; then available="$available exfat"; fi

if [ -z "$available" ]; then
  log '[INST][BLOCKED] No filesystem has both a registered kernel mount driver and a matching formatter'
  missing="$missing filesystem-backend"
else
  log "[INST] Verified filesystem backends:$available"
fi

if [ -n "$missing" ]; then
  progress 95 'BLOCKED' 'Storage preflight incomplete; no installation or formatting permitted'
  log '[INST][BLOCKED] Installer is not ready; resolve the listed storage prerequisites and retry'
  exit 78
fi

progress 65 'Storage' 'Read-only storage preflight passed; no disk modified'
if [ -x "$ROOT/usr/bin/chimera-driver-manager.sh" ]; then
  "$ROOT/usr/bin/chimera-driver-manager.sh" inventory || log '[INST][WARN] Driver inventory command failed'
  "$ROOT/usr/bin/chimera-driver-manager.sh" search || log '[INST][WARN] Driver search command failed'
fi
if [ -x "$ROOT/usr/bin/chimera-logrotate.sh" ]; then
  "$ROOT/usr/bin/chimera-logrotate.sh" || log '[INST][WARN] Log rotation command failed'
fi
progress 80 'Aurora' 'Installer desktop preparation remains a separate runtime gate'
progress 95 'Validation' 'Storage preflight passed; installation actions not executed'
progress 100 'Installer' 'Read-only preflight passed; awaiting explicit installation workflow'
log '[INST] Storage preflight passed; no partition, format, mount or installation operation was performed'
