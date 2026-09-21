#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/chimera-live"
STAGE="$BUILD/iso-root"
OUT="${CHIMERA_OUTPUT_ISO:-$ROOT/build/iso/chimera-ii-os.iso}"
mkdir -p "$STAGE/boot" "$STAGE/install" "$STAGE/system" "$(dirname "$OUT")"
if [[ -n "${CHIMERA_KERNEL:-}" && -f "$CHIMERA_KERNEL" ]]; then cp "$CHIMERA_KERNEL" "$STAGE/boot/koronos.elf"; fi
cp "$ROOT/boot/livecd/live-manifest.json" "$STAGE/boot/"
cp -a "$ROOT/installer" "$STAGE/install/installer-source"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/boot" "$STAGE/system/boot"
command -v grub-mkrescue >/dev/null 2>&1 || { echo "grub-mkrescue is required" >&2; exit 2; }
mkdir -p "$STAGE/boot/grub"
printf "%s\n" 'set timeout=8' 'menuentry "Chimera II OS - Live" { multiboot2 /boot/koronos.elf chimera.mode=live; boot; }' 'menuentry "Chimera II OS - Install" { multiboot2 /boot/koronos.elf chimera.mode=install; boot; }' 'menuentry "Chimera II OS - Safe Graphics" { multiboot2 /boot/koronos.elf chimera.mode=safe-graphics; boot; }' 'menuentry "Chimera II OS - Diagnostics" { multiboot2 /boot/koronos.elf chimera.mode=diagnostics; boot; }' > "$STAGE/boot/grub/grub.cfg"
grub-mkrescue -o "$OUT" "$STAGE"
sha256sum "$OUT" > "$OUT.sha256"
