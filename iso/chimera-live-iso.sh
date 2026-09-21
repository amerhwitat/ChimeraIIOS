#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/chimera-live"
STAGE="$BUILD/iso-root"
OUT="${CHIMERA_OUTPUT_ISO:-$ROOT/build/iso/chimera-ii-os.iso}"
# grub-mkrescue uses mtools/mformat to create the EFI FAT image. Keep its
# temporary FAT image on a native Linux filesystem (important for WSL /mnt/c).
ISO_TMP="${CHIMERA_ISO_TMPDIR:-$(mktemp -d /tmp/chimera-iso.XXXXXX)}"
ISO_TMP_CREATED=1
cleanup() { if [[ "$ISO_TMP_CREATED" == "1" ]]; then rm -rf "$ISO_TMP"; fi; }
trap cleanup EXIT
mkdir -p "$ISO_TMP"
export TMPDIR="$ISO_TMP"
export MTOOLS_SKIP_CHECK=1
mkdir -p "$STAGE/boot" "$STAGE/install" "$STAGE/system" "$(dirname "$OUT")"
copy_if_distinct() {
  local src="$1" dst="$2"
  if [[ -f "$src" && -f "$dst" ]] && [[ "$(readlink -f "$src")" == "$(readlink -f "$dst")" ]]; then
    return 0
  fi
  cp -f "$src" "$dst"
}
if [[ -n "${CHIMERA_KERNEL:-}" && -f "$CHIMERA_KERNEL" ]]; then
  copy_if_distinct "$CHIMERA_KERNEL" "$STAGE/boot/koronos.elf"
fi
cp "$ROOT/boot/livecd/live-manifest.json" "$STAGE/boot/"
cp -a "$ROOT/installer" "$STAGE/install/installer-source"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/boot" "$STAGE/system/boot"
command -v grub-mkrescue >/dev/null 2>&1 || { echo "grub-mkrescue is required" >&2; exit 2; }
command -v mformat >/dev/null 2>&1 || { echo "mtools/mformat is required by grub-mkrescue" >&2; exit 2; }
command -v xorriso >/dev/null 2>&1 || { echo "xorriso is required by grub-mkrescue" >&2; exit 2; }
# Verify mformat can create a FAT image in the native temporary filesystem before
# invoking GRUB. This turns a vague grub-mkrescue failure into a useful error.
MFORMAT_TEST="$ISO_TMP/mformat-test.img"
if ! truncate -s 1440K "$MFORMAT_TEST" || ! mformat -i "$MFORMAT_TEST" -f 1440 :: >/dev/null 2>&1; then
  echo "mformat cannot create a FAT image in $ISO_TMP; check mtools installation and filesystem permissions." >&2
  exit 2
fi
rm -f "$MFORMAT_TEST"
mkdir -p "$STAGE/boot/grub"
printf "%s\n" 'set timeout=8' 'menuentry "Chimera II OS - Live" { multiboot2 /boot/koronos.elf chimera.mode=live; boot; }' 'menuentry "Chimera II OS - Install" { multiboot2 /boot/koronos.elf chimera.mode=install; boot; }' 'menuentry "Chimera II OS - Safe Graphics" { multiboot2 /boot/koronos.elf chimera.mode=safe-graphics; boot; }' 'menuentry "Chimera II OS - Diagnostics" { multiboot2 /boot/koronos.elf chimera.mode=diagnostics; boot; }' > "$STAGE/boot/grub/grub.cfg"
rm -f "$OUT"
grub-mkrescue -o "$OUT" "$STAGE"
sha256sum "$OUT" > "$OUT.sha256"
