#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${CHIMERA_LIVE_BOOT_DIR:-$ROOT/build/live-boot}"
mkdir -p "$OUT/boot/koronos" "$OUT/boot/live" "$OUT/initramfs/root"/{bin,sbin,dev,proc,sys,run,tmp,mnt/chimera,etc} "$OUT/mobile"/{arm64,armv7,x86_64} "$OUT/manifests"
KERNEL="${CHIMERA_LINUX_KERNEL:-}"
if [[ -z "$KERNEL" ]]; then KERNEL="$(find /boot -maxdepth 1 -type f \( -name 'vmlinuz-*' -o -name 'vmlinuz' \) 2>/dev/null | sort -V | tail -n1 || true)"; fi
if [[ -n "$KERNEL" && -f "$KERNEL" ]]; then cp -f "$KERNEL" "$OUT/boot/vmlinuz"; sha256sum "$OUT/boot/vmlinuz" > "$OUT/boot/vmlinuz.sha256"; fi
KORONOS="${CHIMERA_KORONOS_KERNEL:-$ROOT/build/koronos/x86_64/koronos.elf}"
[[ -f "$KORONOS" ]] || KORONOS="$(find "$ROOT/build" "$ROOT/kernel" -type f \( -name 'koronos*.elf' -o -name 'kernel.bin' \) 2>/dev/null | head -n1 || true)"
if [[ -n "$KORONOS" && -f "$KORONOS" ]]; then cp -f "$KORONOS" "$OUT/boot/koronos/koronos.elf"; sha256sum "$OUT/boot/koronos/koronos.elf" > "$OUT/boot/koronos/koronos.elf.sha256"; else echo "ERROR: Koronos ELF64 kernel not found." >&2; exit 2; fi
INIT="$OUT/initramfs/root"
cp "$(command -v busybox)" "$INIT/bin/busybox"
for x in sh mount switch_root echo; do ln -sf busybox "$INIT/bin/$x"; done
cat > "$INIT/init" <<'EOF'
#!/bin/sh
set -eu
mount -t proc proc /proc || true
mount -t sysfs sysfs /sys || true
mount -t devtmpfs devtmpfs /dev || true
mount -t tmpfs tmpfs /run || true
mkdir -p /mnt/chimera
for dev in /dev/sr0 /dev/cdrom /dev/vda /dev/sda /dev/sdb /dev/mmcblk0; do
  [ -e "$dev" ] || continue
  mount -o ro "$dev" /mnt/chimera 2>/dev/null && break
done
if [ -f /mnt/chimera/boot/live/live-manifest.json ]; then
  echo "Chimera II OS Live Media"
  echo "Koronos kernel selected by Jasper/GRUB Multiboot2."
  echo "Koronos kernel: /mnt/chimera/boot/koronos/koronos.elf"
else
  echo "Chimera II OS: live media not found."
fi
exec /bin/sh
EOF
chmod +x "$INIT/init"
(cd "$INIT" && find . -print0 | cpio --null -o -H newc 2>/dev/null | gzip -9) > "$OUT/boot/live/chimera-live-initramfs.img"
sha256sum "$OUT/boot/live/chimera-live-initramfs.img" > "$OUT/boot/live/chimera-live-initramfs.img.sha256"
for arch in arm64 armv7 x86_64; do
  mkdir -p "$OUT/mobile/$arch"
  [[ -f "$KORONOS" ]] && cp -f "$KORONOS" "$OUT/mobile/$arch/koronos-runtime.elf"
  printf '{"schema":"CHM-MOBILE-BOOT-1","architecture":"%s","bootloader":"device-specific","kernel":"device-specific-source-required","koronos_runtime":"koronos-runtime.elf","firmware":"device-specific-source-required","verified_binary_generation":true}\n' "$arch" > "$OUT/mobile/$arch/manifest.json"
done
cat > "$OUT/boot/live/live-manifest.json" <<EOF
{"schema":"CHM-LIVE-KORONOS-1","loader":"Jasper","native_bootloader":"Spit Fire","fallback":"GRUB2","kernel":"/boot/koronos/koronos.elf","kernel_protocol":"Multiboot2","initramfs":"/boot/live/chimera-live-initramfs.img","linux_vmlinuz_required":false,"architectures":["x86_64"]}
EOF
cp "$OUT/boot/live/live-manifest.json" "$OUT/manifests/live-boot.json"
echo "Koronos Live boot artifacts generated in $OUT"
