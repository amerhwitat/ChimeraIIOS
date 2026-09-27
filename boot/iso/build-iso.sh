#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO_ROOT="$ROOT/boot/iso"
DIST="$ISO_ROOT/dist"
WORK="$ISO_ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK/tmp"
export TMPDIR="$WORK/tmp"

printf '%s\n' '[1/7] Build and validate the Koronos Multiboot2 kernel'
"$ROOT/kernel/build-koronos.sh"
KORONOS_ELF="$ROOT/build/koronos/x86_64/koronos.elf"
test -s "$KORONOS_ELF"
command -v grub-file >/dev/null || { echo "grub-file is required." >&2; exit 2; }
grub-file --is-x86-multiboot2 "$KORONOS_ELF"

printf '%s\n' '[2/7] Build and link Spit Fire native stages'
"$ROOT/boot/spitfire/build-spitfire.sh" "$DIST/bootloaders" "$KORONOS_ELF"

printf '%s\n' '[3/7] Prepare ISO tree'
"$ISO_ROOT/prepare-layout.sh"
cp "$DIST/bootloaders/spitfire-sf0-mbr.bin" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-stage2.bin" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-sf1-longmode.o" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-sf2-loader.o" "$DIST/iso/boot/spitfire/"

printf '%s\n' '[4/7] Stage Aurora background, embedded JPEG and boot video'
VISUAL_OUT="$DIST/iso/boot/visual"
mkdir -p "$VISUAL_OUT"
AURORA_SOURCE="${CHIMERA_AURORA_SOURCE:-$ROOT/desktop/aurora/assets/aurora-wayland-glass.svg}"
VIDEO_SOURCE="${CHIMERA_BOOT_VIDEO_SOURCE:-$ROOT/assets/boot/chimera-intro.mp4}"
EMBEDDED_VIDEO="${CHIMERA_BOOT_VIDEO_B64:-$ROOT/assets/boot/chimera-intro.mp4.b64}"
if [[ ! -f "$VIDEO_SOURCE" && ! -f "$EMBEDDED_VIDEO" ]]; then
  echo "ERROR: Chimera boot MP4 is not staged." >&2
  echo "Set CHIMERA_BOOT_VIDEO_SOURCE=/path/to/Chimera-intro.mp4 or provide assets/boot/chimera-intro.mp4.b64." >&2
  exit 2
fi
python3 "$ROOT/tools/boot/prepare-visual-assets.py" \
  --background "$AURORA_SOURCE" \
  --video "$VIDEO_SOURCE" \
  --embedded-video "$EMBEDDED_VIDEO" \
  --output-dir "$VISUAL_OUT" \
  --manifest "$VISUAL_OUT/boot-visual-manifest.json"
cp "$ROOT/boot/visual/boot-visual-manifest.json" "$VISUAL_OUT/source-contract.json"

printf '%s\n' '[5/7] Validate kernel-to-GRUB linkage, graphics and installation contracts'
test -s "$DIST/iso/boot/koronos/koronos.elf"
test -s "$DIST/iso/boot/spitfire/spitfire-stage2.bin"
test -s "$DIST/iso/boot/visual/aurora-background.jpg"
test -s "$DIST/iso/boot/visual/aurora-background.jpg.b64"
test -s "$DIST/iso/boot/visual/chimera-intro.mp4"
test -s "$DIST/iso/boot/visual/boot-visual-manifest.json"
test -s "$DIST/iso/boot/grub/aurora-wayland-glass.png"
test -s "$DIST/iso/boot/jasper/background.png"
test -s "$DIST/iso/boot/spitfire/background.png"
test -s "$DIST/iso/install/installer-background.png"
grep -q 'multiboot2 /boot/koronos/koronos.elf' "$ROOT/boot/iso/grub.cfg"
grep -q 'background_image --mode stretch /boot/visual/aurora-background.jpg' "$ROOT/boot/iso/grub.cfg"
grep -q '"native_execution_order"' "$DIST/iso/boot/chimera/manifests/boot-execution-order.json"

test -s "$DIST/iso/boot/live/chimera-live-initramfs.img" || { echo "Live initramfs missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/live/live-manifest.json" || { echo "Live manifest missing from ISO staging tree." >&2; exit 1; }
grep -q '/boot/live/chimera-live-initramfs.img' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/live/live-manifest.json' "$ROOT/boot/jasper/live.cfg"

for contract in \
  "$DIST/iso/install/installer/installation.img" \
  "$DIST/iso/install/installer/installation-manifest.json" \
  "$DIST/iso/install/installer/installer-contract.json" \
  "$DIST/iso/install/installer/installation_phases.json" \
  "$DIST/iso/install/installer/installer_profiles.json"; do
  if [[ ! -s "$contract" ]]; then
    echo "ERROR: required installer contract missing: $contract" >&2
    exit 2
  fi
done

python3 "$ISO_ROOT/validate-iso.py" --tree "$DIST/iso" --write-manifest "$DIST/iso/checksums/SHA256SUMS"

printf '%s\n' '[6/7] Master BIOS + UEFI hybrid ISO'
command -v grub-mkrescue >/dev/null || { echo "grub-mkrescue is required." >&2; exit 2; }
command -v xorriso >/dev/null || { echo "xorriso is required." >&2; exit 2; }
# Large-capacity ISO: ISO9660 level 3 removes the legacy CD-size/file-size
# assumptions. The resulting image is intended for DVD/USB/VM media.
grub-mkrescue \
  -o "$DIST/output.iso" \
  -iso-level 3 \
  -joliet \
  -rockridge \
  "$DIST/iso"
test -s "$DIST/output.iso"
sha256sum "$DIST/output.iso" | tee "$DIST/output.iso.sha256"

printf '%s\n' '[7/7] Inspect El Torito boot records'
xorriso -indev "$DIST/output.iso" -report_el_torito plain -report_system_area plain | tee "$DIST/ISO-BOOT-REPORT.txt"
printf 'ISO: %s\nKoronos: %s\nSpit Fire: %s\nAurora background: %s\nBoot video: %s\n' \
  "$DIST/output.iso" "$DIST/iso/boot/koronos/koronos.elf" "$DIST/iso/boot/spitfire/spitfire-stage2.bin" \
  "$DIST/iso/boot/visual/aurora-background.jpg" "$DIST/iso/boot/visual/chimera-intro.mp4"
