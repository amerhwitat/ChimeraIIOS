#!/bin/sh
set +e
say(){ printf '%s\\n' "$*"; }
target_fs(){
  case "$1" in
    linux) echo "ext4 xfs btrfs zfs vfat exfat ntfs3 luks2 lvm mdraid";;
    windows) echo "ntfs3 vfat exfat";;
    macos|osx) echo "apfs hfsplus hfs vfat exfat";;
    chimera) echo "qfs ext4 xfs btrfs zfs vfat exfat ntfs3 iso9660 udf squashfs";;
    *) echo "";;
  esac
}
show_targets(){
  say "Chimera recovery runtime targets:"
  say "  linux    : $(target_fs linux)"
  say "  windows  : $(target_fs windows)"
  say "  macos/osx: $(target_fs macos)"
  say "  chimera  : $(target_fs chimera)"
  say "Default mount policy: read-only."
}
detect(){
  command -v blkid >/dev/null 2>&1 && blkid 2>/dev/null || true
  say "APFS/BitLocker volumes are detection/reporting targets; encryption/security is not bypassed."
}
mount_fs(){
  dev="$1"; fs="$2"; mode="${3:-ro}"
  [ -b "$dev" ] || { say "Usage: mount-fs /dev/<device> <filesystem> [ro|rw]"; return 2; }
  [ "$mode" = rw ] || mode=ro
  mkdir -p /mnt/chimera-target
  if [ "$fs" = apfs ] && ! grep -qw apfs /proc/filesystems 2>/dev/null; then
    say "APFS implementation unavailable in this recovery kernel; detection only."
    return 1
  fi
  say "Mounting $dev as $fs ($mode)."
  mount -t "$fs" -o "$mode" "$dev" /mnt/chimera-target || return 1
  say "Mounted at /mnt/chimera-target"
}
case "${1:-targets}" in
  targets) show_targets;;
  detect) detect;;
  mount-fs) shift; mount_fs "$@";;
  *) say "Usage: targets | detect | mount-fs <device> <filesystem> [ro|rw]";;
esac
