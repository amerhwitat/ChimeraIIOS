
chimera_copy_if_distinct() {
    local src="$1"
    local dst="$2"

    mkdir -p "$(dirname "$dst")"

    local src_real dst_real
    src_real="$(realpath -m "$src")"
    dst_real="$(realpath -m "$dst")"

    if [[ "$src_real" == "$dst_real" ]]; then
        echo "[CHIMERA] SKIP self-copy: $src_real"
        return 0
    fi

    cp -f -- "$src" "$dst"
}
#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/boot/chimera-recovery-console.sh

Usage:
  tools/boot/chimera-recovery-console.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
# Chimera II OS early-boot recovery console.
# Runs from the recovery initramfs and deliberately avoids destructive actions
# unless the operator explicitly selects a repair command.

set +e

say() { printf '%s\n' "$*"; }

find_root() {
    for d in /dev/mapper/chimera-root /dev/chimera-root /dev/sda2 /dev/sda1 /dev/vda2 /dev/vda1 /dev/nvme0n1p2 /dev/nvme0n1p1; do
        [ -b "$d" ] && { echo "$d"; return 0; }
    done
    return 1
}

mount_root() {
    dev="${1:-}"
    mode="${2:-ro}"
    [ -n "$dev" ] || dev="$(find_root)"
    [ -n "$dev" ] || { say "[RECOVERY] No candidate root device found."; return 1; }
    mkdir -p /mnt/chimera-root
    if mount | grep -q ' /mnt/chimera-root '; then
        say "[RECOVERY] Root is already mounted at /mnt/chimera-root."
        return 0
    fi
    say "[RECOVERY] Mounting $dev ($mode)..."
    mount -o "$mode" "$dev" /mnt/chimera-root || {
        say "[RECOVERY] Mount failed. Try: disks, then mount-root <device> ro"
        return 1
    }
    say "[RECOVERY] Root mounted at /mnt/chimera-root"
}

unmount_root() {
    umount /mnt/chimera-root 2>/dev/null || true
    say "[RECOVERY] Root unmounted."
}

show_help() {
    cat <<'EOF'
Chimera II OS — Jasper/Koronos Recovery Console

Information:
  help                 Show this help
  status               Show recovery, kernel and mount state
  disks                List block devices and filesystems
  mounts               Show current mounts
  logs                 Show Chimera early-boot log
  dmesg                Show kernel messages when available
  drivers              Run the Chimera driver inventory
  network              Show network interfaces/routes
  targets              Show Linux/Windows/macOS/Chimera runtime targets
  target-detect        Detect filesystems and encrypted/platform volumes
  mount-fs <dev> <fs> [ro|rw]  Explicit filesystem mount
  mount-target <target>  Select target family and scan

Filesystem:
  mount-root [dev] [rw|ro]  Mount installed root at /mnt/chimera-root
  umount-root               Unmount installed root
  check-root [dev]          Non-destructive filesystem check when supported
  repair-root [dev]         Interactive filesystem repair (destructive)

Boot/recovery:
  verify                  Verify key Chimera boot files on the mounted root
  boot-normal             Attempt to switch into the installed Chimera root
  rollback                Display available Chimera rollback/checkpoint data
  shell                   Drop to the underlying BusyBox shell
  reboot                  Reboot the machine
  poweroff                Power off the machine
  exit                    Leave the recovery console

Recovery is intentionally conservative: check-root does not modify disks;
repair-root requires an explicit confirmation before running fsck -fy.
EOF
}

status() {
    say "[RECOVERY] Chimera II OS recovery environment"
    say "[RECOVERY] Kernel: $(uname -a 2>/dev/null || echo unavailable)"
    say "[RECOVERY] Initramfs: ${CHIMERA_RECOVERY_INITRAMFS:-yes}"
    say "[RECOVERY] Root: $(find_root 2>/dev/null || echo not-detected)"
    mounts
}

mounts() { mount 2>/dev/null || cat /proc/mounts 2>/dev/null; }

disks() {
    if command -v blkid >/dev/null 2>&1; then blkid 2>/dev/null || true; fi
    ls -l /dev/sd* /dev/vd* /dev/xvd* /dev/nvme* /dev/mmcblk* /dev/mapper/* 2>/dev/null || true
}

logs() {
    for f in /var/log/mesgs /var/log/messages /run/initramfs/init.log; do
        [ -f "$f" ] && { say "===== $f ====="; tail -n 200 "$f"; }
    done
}

target_helpers() {
    if [ -f /bin/chimera-recovery-targets.sh ]; then sh /bin/chimera-recovery-targets.sh "$@"; else say "[RECOVERY] Target helper unavailable."; fi
}

drivers() {
    if [ -x /bin/chimera-driver-manager.sh ]; then
        /bin/chimera-driver-manager.sh inventory || true
    else
        say "[RECOVERY] Driver manager not present in initramfs."
    fi
}

network() {
    ip addr 2>/dev/null || true
    ip route 2>/dev/null || true
}

check_root() {
    dev="${1:-$(find_root 2>/dev/null)}"
    [ -b "$dev" ] || { say "Usage: check-root /dev/<partition>"; return 1; }
    say "[RECOVERY] Read-only filesystem check: $dev"
    fsck -fn "$dev"
}

repair_root() {
    dev="${1:-$(find_root 2>/dev/null)}"
    [ -b "$dev" ] || { say "Usage: repair-root /dev/<partition>"; return 1; }
    say "WARNING: repair-root may modify filesystem metadata on $dev."
    printf 'Type REPAIR to continue: '
    read answer
    [ "$answer" = "REPAIR" ] || { say "[RECOVERY] Repair cancelled."; return 1; }
    umount /mnt/chimera-root 2>/dev/null || true
    fsck -fy "$dev"
}

verify() {
    [ -d /mnt/chimera-root ] || { say "[RECOVERY] Mount the root first."; return 1; }
    for f in /boot/koronos/koronos.elf /boot/jasper/jasper.elf /boot/jasper/jasper.cfg /boot/live/live-manifest.json; do
        if [ -e "/mnt/chimera-root$f" ]; then say "[OK] $f"; else say "[MISSING] $f"; fi
    done
}

rollback() {
    [ -d /mnt/chimera-root ] || { say "[RECOVERY] Mount the root first."; return 1; }
    for d in /var/lib/chimera/rollback /var/lib/chimera/checkpoints /boot/chimera/recovery /boot/recovery; do
        if [ -e "/mnt/chimera-root$d" ]; then
            say "===== $d ====="; ls -la "/mnt/chimera-root$d" 2>/dev/null || true
        fi
    done
}

boot_normal() {
    [ -d /mnt/chimera-root ] || mount_root "" rw || return 1
    [ -x /mnt/chimera-root/sbin/init ] || [ -x /mnt/chimera-root/bin/init ] || {
        say "[RECOVERY] Installed init was not found. Use verify and logs."; return 1;
    }
    say "[RECOVERY] Preparing switch_root to /mnt/chimera-root"
    mount --bind /dev /mnt/chimera-root/dev 2>/dev/null || true
    mount --bind /proc /mnt/chimera-root/proc 2>/dev/null || true
    mount --bind /sys /mnt/chimera-root/sys 2>/dev/null || true
    mount --bind /run /mnt/chimera-root/run 2>/dev/null || true
    if command -v switch_root >/dev/null 2>&1; then
        exec switch_root /mnt/chimera-root /sbin/init
    fi
    say "[RECOVERY] switch_root is unavailable in this initramfs."
}

show_help
while :; do
    printf '\nchimera-recovery> '
    read cmd arg1 arg2 rest || { say; break; }
    case "$cmd" in
        ""|help|?) show_help ;;
        status) status ;;
        disks|lsblk) disks ;;
        mounts|mount) mounts ;;
        logs|log) logs ;;
        dmesg) dmesg 2>/dev/null || true ;;
        drivers) drivers ;;
        network|net) network ;;
        targets) target_helpers targets ;;
        target-detect) target_helpers detect ;;
        mount-fs) target_helpers mount-fs "$arg1" "$arg2" "${rest:-ro}" ;;
        mount-target) target_helpers targets; target_helpers detect ;;
        mount-root) mount_root "$arg1" "$arg2" ;;
        umount-root) unmount_root ;;
        check-root) check_root "$arg1" ;;
        repair-root) repair_root "$arg1" ;;
        verify) verify ;;
        rollback) rollback ;;
        boot-normal|continue) boot_normal ;;
        shell) /bin/sh ;;
        reboot) reboot -f 2>/dev/null || busybox reboot -f ;;
        poweroff|halt) poweroff -f 2>/dev/null || busybox poweroff -f ;;
        exit|quit) break ;;
        *) say "Unknown command: $cmd — type help" ;;
    esac
done

say "[RECOVERY] Console exited; remaining in recovery environment."
exec /bin/sh
