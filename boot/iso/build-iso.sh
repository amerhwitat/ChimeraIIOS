#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: boot/iso/build-iso.sh

Usage:
  boot/iso/build-iso.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

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

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO_ROOT="$ROOT/boot/iso"
DIST="$ISO_ROOT/dist"
WORK="$ISO_ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK/tmp"
export TMPDIR="$WORK/tmp"

printf '%s\n' '[1/7] Build and validate the Koronos Multiboot2 kernel'
bash "$ROOT/kernel/build-koronos.sh"
KORONOS_ELF="$ROOT/build/koronos/x86_64/koronos.elf"
test -s "$KORONOS_ELF"
command -v grub-file >/dev/null || { echo "grub-file is required." >&2; exit 2; }
grub-file --is-x86-multiboot2 "$KORONOS_ELF"

printf '%s\n' '[2/7] Build and link Spit Fire native stages'
bash "$ROOT/boot/spitfire/build-spitfire.sh" "$DIST/bootloaders" "$KORONOS_ELF"

printf '%s\n' '[3/7] Prepare ISO tree — canonical Spit Fire → Jasper/GRUB → Koronos pipeline'
bash "$ISO_ROOT/prepare-layout.sh"
# The build is intentionally anchored to the canonical native handoff order.
# Do not substitute the obsolete aurora-background.jpg contract or bypass
# Koronos in order to start Aurora directly from ISO boot.
test -s "$ROOT/boot/boot-pipeline-contract.json" || { echo "ERROR: canonical boot pipeline contract missing." >&2; exit 2; }
cp "$DIST/bootloaders/spitfire-sf0-mbr.bin" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-stage2.bin" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-sf1-longmode.o" "$DIST/iso/boot/spitfire/"
cp "$DIST/bootloaders/spitfire-sf2-loader.o" "$DIST/iso/boot/spitfire/"

# Jasper recovery is a real early-userspace terminal, not only a menu label.
# Stage its dedicated initramfs and the canonical recovery menu after
# prepare-layout, whose legacy recovery.cfg generation is intentionally kept
# compatible with older installations.
RECOVERY_BOOT="$ROOT/build/live-boot/boot/recovery"
test -s "$RECOVERY_BOOT/chimera-recovery-initramfs.img" || { echo "ERROR: Jasper recovery initramfs missing: $RECOVERY_BOOT/chimera-recovery-initramfs.img" >&2; exit 2; }
test -s "$RECOVERY_BOOT/recovery-manifest.json" || { echo "ERROR: Jasper recovery manifest missing: $RECOVERY_BOOT/recovery-manifest.json" >&2; exit 2; }
mkdir -p "$DIST/iso/boot/recovery"
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.img" "$DIST/iso/boot/recovery/"
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.img.sha256" "$DIST/iso/boot/recovery/" 2>/dev/null || true
cp -f "$RECOVERY_BOOT/recovery-manifest.json" "$DIST/iso/boot/recovery/"
cp -f "$ROOT/boot/jasper/recovery.cfg" "$DIST/iso/boot/jasper/recovery.cfg"

printf '%s\n' '[4/7] Stage complete Aurora artwork, Init.mp4 and professional progress UI'
VISUAL_OUT="$DIST/iso/boot/visual"
mkdir -p "$VISUAL_OUT"
bash "$ROOT/tools/aurora/build-visual-assets.sh" "$ROOT/build/aurora-media"
MEDIA="$ROOT/build/aurora-media"
test -s "$MEDIA/Init.mp4" || { echo "ERROR: Aurora Init.mp4 was not generated or supplied." >&2; exit 2; }
mkdir -p "$DIST/iso/boot/visual/aurora-media"
cp -a "$MEDIA/." "$DIST/iso/boot/visual/aurora-media/"
for f in   backgrounds/boot.png   backgrounds/desktop.png   menus/default.png   splash/aurora-splash.png   installer/aurora-installer.png   recovery/aurora-recovery.png   diagnostics/aurora-diagnostics.png   live/aurora-live.png   mobile/aurora-mobile.png   manifest.json   progress/state.json   progress/stages.json   progress/style.json   Init.mp4; do
  test -s "$MEDIA/$f" || { echo "ERROR: Aurora asset missing: $MEDIA/$f" >&2; exit 2; }
done
cp -f "$MEDIA/backgrounds/boot.png" "$VISUAL_OUT/aurora-boot.png"
cp -f "$MEDIA/backgrounds/desktop.png" "$VISUAL_OUT/aurora-desktop.png"
cp -f "$MEDIA/menus/default.png" "$VISUAL_OUT/aurora-menu.png"
cp -f "$MEDIA/splash/aurora-splash.png" "$VISUAL_OUT/aurora-splash.png"
cp -f "$MEDIA/installer/aurora-installer.png" "$VISUAL_OUT/aurora-installer.png"
cp -f "$MEDIA/recovery/aurora-recovery.png" "$VISUAL_OUT/aurora-recovery.png"
cp -f "$MEDIA/diagnostics/aurora-diagnostics.png" "$VISUAL_OUT/aurora-diagnostics.png"
cp -f "$MEDIA/live/aurora-live.png" "$VISUAL_OUT/aurora-live.png"
cp -f "$MEDIA/mobile/aurora-mobile.png" "$VISUAL_OUT/aurora-mobile.png"
cp -f "$MEDIA/manifest.json" "$VISUAL_OUT/aurora-manifest.json"
cp -f "$MEDIA/progress/"*.json "$VISUAL_OUT/"
cp -f "$MEDIA/Init.mp4" "$VISUAL_OUT/Init.mp4"

# Hard-stage the same deterministic artwork/media in every native boot namespace.
# This prevents Spit Fire/Jasper/GRUB from depending on a later rootfs mount.
for stage in spitfire jasper grub koronos; do
  mkdir -p "$DIST/iso/boot/$stage"
  cp -f "$MEDIA/Init.mp4" "$DIST/iso/boot/$stage/Init.mp4"
  cp -f "$MEDIA/backgrounds/boot.png" "$DIST/iso/boot/$stage/aurora-boot.png"
done
cp -f "$ROOT/boot/splash/spitfire_background.svg" "$DIST/iso/boot/spitfire/"
cp -f "$ROOT/boot/splash/jasper_background.svg" "$DIST/iso/boot/jasper/"
cp -f "$ROOT/boot/splash/aurora_boot_splash.svg" "$DIST/iso/boot/grub/"
cp -f "$ROOT/boot/splash/aurora_boot_splash.svg" "$DIST/iso/boot/koronos/"
cp -f "$ROOT/boot/boot-artwork-manifest.json" "$DIST/iso/boot/spitfire/"
cp -f "$ROOT/boot/boot-artwork-manifest.json" "$DIST/iso/boot/jasper/"
cp -f "$ROOT/boot/boot-artwork-manifest.json" "$DIST/iso/boot/grub/"
cp -f "$ROOT/boot/boot-artwork-manifest.json" "$DIST/iso/boot/koronos/"
cp -f "$ROOT/boot/boot-pipeline-contract.json" "$DIST/iso/boot/chimera/manifests/boot-pipeline-contract.json"
# Mirror the same contract into the installed/live Aurora runtime when a rootfs is present.
RUNTIME_AURORA_ROOT="${CHIMERA_ROOTFS_DIR:-$ROOT/build/rootfs}/usr/share/chimera/aurora"
if [[ -d "$(dirname "$RUNTIME_AURORA_ROOT")" ]]; then
  mkdir -p "$RUNTIME_AURORA_ROOT"
  cp -a "$MEDIA/." "$RUNTIME_AURORA_ROOT/"
fi
printf '%s\n' '[5/7] Validate canonical Spit Fire → Jasper/GRUB → Koronos → userspace → Aurora contracts'
python3 - "$ROOT/boot/boot-pipeline-contract.json" "$ROOT/boot/iso/grub.cfg" <<'PY'
import json, pathlib, sys
contract = json.loads(pathlib.Path(sys.argv[1]).read_text())
grub = pathlib.Path(sys.argv[2]).read_text()
stages = [x["stage"] for x in contract["pipeline"]]
expected = ["Spit Fire", "Jasper/GRUB", "Koronos ELF", "hardware/driver initialization", "scheduler/runtime loop", "live/recovery/installer userspace", "Aurora"]
if stages != expected:
    raise SystemExit(f"ERROR: canonical boot stage order changed: {stages}")
if "multiboot2 /boot/koronos/koronos.elf" not in grub:
    raise SystemExit("ERROR: GRUB does not hand off through the canonical Koronos ELF.")
for obsolete in contract["artwork_contract"]["forbidden_obsolete_paths"]:
    if obsolete in grub:
        raise SystemExit(f"ERROR: obsolete artwork path referenced by GRUB: {obsolete}")
PY

test -s "$DIST/iso/boot/koronos/koronos.elf"
test -s "$DIST/iso/boot/spitfire/spitfire-stage2.bin"
for visual in \
  aurora-boot.png aurora-menu.png aurora-splash.png aurora-installer.png \
  aurora-recovery.png aurora-diagnostics.png aurora-live.png aurora-mobile.png \
  aurora-desktop.png Init.mp4 aurora-manifest.json state.json stages.json style.json; do
  test -s "$DIST/iso/boot/visual/$visual" || { echo "ERROR: Aurora visual asset missing: $visual" >&2; exit 2; }
done
test -s "$DIST/iso/boot/visual/aurora-media/manifest.json"
test -s "$DIST/iso/boot/chimera/manifests/boot-pipeline-contract.json"
! grep -R -F 'aurora-background.jpg' "$DIST/iso" >/dev/null || { echo "ERROR: obsolete aurora-background.jpg artwork contract leaked into ISO." >&2; exit 2; }
for stage in spitfire jasper grub koronos; do
  test -s "$DIST/iso/boot/$stage/Init.mp4" || { echo "ERROR: Init.mp4 missing from $stage stage." >&2; exit 2; }
  test -s "$DIST/iso/boot/$stage/aurora-boot.png" || { echo "ERROR: Aurora artwork missing from $stage stage." >&2; exit 2; }
  test -s "$DIST/iso/boot/$stage/boot-artwork-manifest.json" || { echo "ERROR: artwork manifest missing from $stage stage." >&2; exit 2; }
done

# Stage a real installer initramfs and the canonical installer JSON contracts.
bash "$ROOT/tools/chimera-stage-installer-media.sh" "$DIST/iso"

grep -q 'multiboot2 /boot/koronos/koronos.elf' "$ROOT/boot/iso/grub.cfg"
grep -q 'background_image --mode stretch /boot/visual/aurora-boot.png' "$ROOT/boot/iso/grub.cfg"
grep -q '"native_execution_order"' "$DIST/iso/boot/chimera/manifests/boot-execution-order.json"

test -s "$DIST/iso/boot/live/chimera-live-initramfs.img" || { echo "Live initramfs missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/live/live-manifest.json" || { echo "Live manifest missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/recovery/chimera-recovery-initramfs.img" || { echo "Recovery initramfs missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/recovery/recovery-manifest.json" || { echo "Recovery manifest missing from ISO staging tree." >&2; exit 1; }
grep -q '/boot/live/chimera-live-initramfs.img' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/live/live-manifest.json' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/recovery/chimera-recovery-initramfs.img' "$ROOT/boot/jasper/recovery.cfg"
grep -q 'Recovery Terminal' "$ROOT/boot/jasper/recovery.cfg"

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
  -R \
  "$DIST/iso"
test -s "$DIST/output.iso"
sha256sum "$DIST/output.iso" | tee "$DIST/output.iso.sha256"

printf '%s\n' '[7/7] Inspect El Torito boot records'
xorriso -indev "$DIST/output.iso" -report_el_torito plain -report_system_area plain | tee "$DIST/ISO-BOOT-REPORT.txt"
printf 'ISO: %s\nKoronos: %s\nSpit Fire: %s\nAurora background: %s\nBoot video: %s\nRecovery terminal: %s\n' \
  "$DIST/output.iso" "$DIST/iso/boot/koronos/koronos.elf" "$DIST/iso/boot/spitfire/spitfire-stage2.bin" \
  "$DIST/iso/boot/visual/aurora-boot.png" "$DIST/iso/boot/visual/Init.mp4" \
  "$DIST/iso/boot/recovery/chimera-recovery-initramfs.img"
