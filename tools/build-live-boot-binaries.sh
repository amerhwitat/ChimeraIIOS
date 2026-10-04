#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-live-boot-binaries.sh

Usage:
  tools/build-live-boot-binaries.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# Always inherit the canonical build directory selected by build-chimera-iso.sh.
# CHIMERA_LIVE_BOOT_DIR remains an explicit override for standalone builds.
BUILD_DIR="${CHIMERA_BUILD_DIR:-$ROOT/build}"
OUT="${CHIMERA_LIVE_BOOT_DIR:-$BUILD_DIR/live-boot}"
mkdir -p "$OUT/boot/koronos" "$OUT/boot/live" "$OUT/boot/recovery" "$OUT/initramfs/root"/{bin,sbin,dev,proc,sys,run,tmp,mnt/chimera,etc,var/log/mesgs/archive,var/lib/chimera/drivers,etc/chimera/drivers,lib/chimera/drivers,lib/firmware} "$OUT/mobile"/{arm64,armv7,x86_64} "$OUT/manifests"
KERNEL="${CHIMERA_LINUX_KERNEL:-}"
if [[ -z "$KERNEL" ]]; then KERNEL="$(find /boot -maxdepth 1 -type f \( -name 'vmlinuz-*' -o -name 'vmlinuz' \) 2>/dev/null | sort -V | tail -n1 || true)"; fi
if [[ -n "$KERNEL" && -f "$KERNEL" ]]; then cp -f "$KERNEL" "$OUT/boot/vmlinuz"; sha256sum "$OUT/boot/vmlinuz" > "$OUT/boot/vmlinuz.sha256"; fi
KORONOS="${CHIMERA_KORONOS_KERNEL:-$BUILD_DIR/koronos/x86_64/koronos.elf}"
[[ -f "$KORONOS" ]] || KORONOS="$(find "$BUILD_DIR" "$ROOT/kernel" -type f \( -name 'koronos*.elf' -o -name 'kernel.bin' \) 2>/dev/null | head -n1 || true)"
if [[ -n "$KORONOS" && -f "$KORONOS" ]]; then cp -f "$KORONOS" "$OUT/boot/koronos/koronos.elf"; sha256sum "$OUT/boot/koronos/koronos.elf" > "$OUT/boot/koronos/koronos.elf.sha256"; else echo "ERROR: Koronos ELF64 kernel not found." >&2; exit 2; fi
INIT="$OUT/initramfs/root"
BUSYBOX="$(command -v busybox || true)"
[[ -n "$BUSYBOX" ]] || { echo "ERROR: busybox is required to build the live/recovery initramfs." >&2; exit 2; }
cp -f "$BUSYBOX" "$INIT/bin/busybox"
for x in sh mount umount switch_root echo printf ps top tail date clear sed awk head cat ls grep find sleep uname dmesg blkid fsck ip route reboot poweroff gzip; do ln -sf busybox "$INIT/bin/$x"; done
for f in tools/chimera-driver-manager.sh tools/chimera-logrotate.sh tools/boot/chimera-recovery-console.sh tools/boot/chimera-recovery-targets.sh; do [[ -f "$ROOT/$f" ]] && cp -f "$ROOT/$f" "$INIT/bin/"; done
[[ -f "$ROOT/config/drivers/driver-repositories.json" ]] && cp -f "$ROOT/config/drivers/driver-repositories.json" "$INIT/etc/chimera/drivers/"
[[ -f "$ROOT/config/drivers/driver-policy.json" ]] && cp -f "$ROOT/config/drivers/driver-policy.json" "$INIT/etc/chimera/drivers/"
[[ -f "$ROOT/config/recovery/chimera-recovery-targets.json" ]] && cp -f "$ROOT/config/recovery/chimera-recovery-targets.json" "$INIT/etc/chimera/"
cat > "$INIT/init" <<'EOF'
#!/bin/sh
set -eu
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t tmpfs tmpfs /run 2>/dev/null || true
mkdir -p /mnt/chimera /var/log/mesgs/archive /var/lib/chimera/drivers
ln -sfn /var/log/mesgs /var/log/messages 2>/dev/null || true
printf "[LIVE] Initramfs started\\n" >> /var/log/mesgs
if [ -x /bin/chimera-driver-manager.sh ]; then /bin/chimera-driver-manager.sh inventory || true; fi

mounted=0
i=0
while [ "$i" -lt 30 ]; do
  for dev in /dev/sr0 /dev/cdrom /dev/vda /dev/sda /dev/sdb /dev/mmcblk0; do
    [ -b "$dev" ] || continue
    if mount -t iso9660 -o ro "$dev" /mnt/chimera 2>/dev/null; then mounted=1; break 2; fi
    if mount -o ro "$dev" /mnt/chimera 2>/dev/null; then mounted=1; break 2; fi
  done
  i=$((i + 1)); sleep 1
done

if [ "$mounted" -eq 1 ] && [ -f /mnt/chimera/boot/live/live-manifest.json ]; then
  printf "[LIVE] Media mounted\\n" >> /var/log/mesgs
  echo "Chimera II OS Live Media"
  echo "Koronos kernel selected by Jasper/GRUB Multiboot2."
  echo "Koronos kernel: /mnt/chimera/boot/koronos/koronos.elf"
  echo "Live manifest: /mnt/chimera/boot/live/live-manifest.json"
  echo "Live initramfs: /mnt/chimera/boot/live/chimera-live-initramfs.img"
else
  printf "[LIVE] Media not found after 30 seconds\\n" >> /var/log/mesgs
  echo "Chimera II OS: live media not found after 30 seconds."
  echo "Available block devices:"
  ls -l /dev/sr* /dev/vd* /dev/sd* /dev/mmcblk* 2>/dev/null || true
fi
exec /bin/sh
EOF
chmod +x "$INIT/init" "$INIT/bin/chimera-recovery-console.sh" 2>/dev/null || true
(cd "$INIT" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9) > "$OUT/boot/live/chimera-live-initramfs.img"
sha256sum "$OUT/boot/live/chimera-live-initramfs.img" > "$OUT/boot/live/chimera-live-initramfs.img.sha256"

# Dedicated recovery image: same hardware/filesystem utilities as Live, but
# the init process immediately opens the repair console instead of attempting
# to mount optical media. This makes Jasper Recovery deterministic.
REC="$OUT/initramfs/recovery"
rm -rf "$REC"
mkdir -p "$REC"
cp -a "$INIT/." "$REC/"
cat > "$REC/init" <<'EOF'
#!/bin/sh
set -eu
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mount -t tmpfs tmpfs /run 2>/dev/null || true
mkdir -p /mnt/chimera-root /var/log/mesgs/archive /var/lib/chimera/drivers
ln -sfn /var/log/mesgs /var/log/messages 2>/dev/null || true
printf '%s\\n' '[RECOVERY] Jasper/Koronos recovery initramfs started' >> /var/log/mesgs
export CHIMERA_RECOVERY_INITRAMFS=1
if [ -x /bin/chimera-driver-manager.sh ]; then /bin/chimera-driver-manager.sh inventory || true; fi
exec /bin/chimera-recovery-console.sh
EOF
chmod +x "$REC/init" "$REC/bin/chimera-recovery-console.sh"
(cd "$REC" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9) > "$OUT/boot/recovery/chimera-recovery-initramfs.img"
sha256sum "$OUT/boot/recovery/chimera-recovery-initramfs.img" > "$OUT/boot/recovery/chimera-recovery-initramfs.img.sha256"

for arch in arm64 armv7 x86_64; do
  mkdir -p "$OUT/mobile/$arch"
  [[ -f "$KORONOS" ]] && cp -f "$KORONOS" "$OUT/mobile/$arch/koronos-runtime.elf"
  printf '{"schema":"CHM-MOBILE-BOOT-1","architecture":"%s","bootloader":"device-specific","kernel":"device-specific-source-required","koronos_runtime":"koronos-runtime.elf","firmware":"device-specific-source-required","verified_binary_generation":true}\n' "$arch" > "$OUT/mobile/$arch/manifest.json"
done
cat > "$OUT/boot/live/live-manifest.json" <<EOF
{"schema":"CHM-LIVE-KORONOS-1","loader":"Jasper","native_bootloader":"Spit Fire","fallback":"GRUB2","kernel":"/boot/koronos/koronos.elf","kernel_protocol":"Multiboot2","initramfs":"/boot/live/chimera-live-initramfs.img","linux_vmlinuz_required":false,"architectures":["x86_64"]}
EOF
cat > "$OUT/boot/recovery/recovery-manifest.json" <<EOF
{"schema":"CHM-RECOVERY-BOOT-2","loader":"Jasper","kernel":"/boot/koronos/koronos.elf","kernel_protocol":"Multiboot2","initramfs":"/boot/recovery/chimera-recovery-initramfs.img","console":"/bin/chimera-recovery-console.sh","operations":["status","disks","mounts","mount-root","umount-root","targets","target-detect","mount-target","mount-fs","check-root","repair-root","verify","rollback","boot-normal","network","drivers","logs"],"runtime_levels":["L0-firmware","L1-koronos","L2-linux","L2-windows","L2-macos","L3-hosted"],"targets":["linux","windows","macos","chimera"]}
EOF
cp "$OUT/boot/live/live-manifest.json" "$OUT/manifests/live-boot.json"
cp "$OUT/boot/recovery/recovery-manifest.json" "$OUT/manifests/recovery-boot.json"
echo "Koronos Live boot artifacts generated in $OUT"
echo "Jasper Recovery initramfs generated in $OUT/boot/recovery"
