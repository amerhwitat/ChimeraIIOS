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
python3 "$ROOT/tools/commands/generate_runtime_manifest.py"
# Canonical system block-size contract. Forward this unchanged into the kernel
# build and all downstream ISO stages; never silently accept malformed values.
CHIMERA_SYSTEM_BLOCK_SIZE="${CHIMERA_SYSTEM_BLOCK_SIZE:-${SYSTEM_BLOCK_SIZE:-4096}}"
if [[ ! "$CHIMERA_SYSTEM_BLOCK_SIZE" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: CHIMERA_SYSTEM_BLOCK_SIZE must be a positive integer (got: $CHIMERA_SYSTEM_BLOCK_SIZE)" >&2
  exit 2
fi
export CHIMERA_SYSTEM_BLOCK_SIZE SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE"
ISO_ROOT="$ROOT/boot/iso"
DIST="$ISO_ROOT/dist"
WORK="$ISO_ROOT/work"
rm -rf "$DIST" "$WORK"
mkdir -p "$DIST" "$WORK/tmp"
export TMPDIR="$WORK/tmp"

printf '%s\n' '[1/7] Build and validate the Koronos Multiboot2 kernel'
CHIMERA_SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE" SYSTEM_BLOCK_SIZE="$CHIMERA_SYSTEM_BLOCK_SIZE" bash "$ROOT/kernel/build-koronos.sh"
KORONOS_ELF="$ROOT/build/koronos/x86_64/koronos.elf"
test -s "$KORONOS_ELF"
command -v grub-file >/dev/null || { echo "grub-file is required." >&2; exit 2; }
grub-file --is-x86-multiboot2 "$KORONOS_ELF"

printf '%s\n' '[2/7] Build and link Spit Fire native stages'
bash "$ROOT/boot/spitfire/build-spitfire.sh" "$DIST/bootloaders" "$KORONOS_ELF"

printf '%s\n' '[3/7] Prepare ISO tree'
bash "$ISO_ROOT/prepare-layout.sh"
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
test -s "$RECOVERY_BOOT/chimera-recovery-initramfs.cpio" || { echo "ERROR: Jasper recovery CPIO VFS archive missing: $RECOVERY_BOOT/chimera-recovery-initramfs.cpio" >&2; exit 2; }
test -s "$RECOVERY_BOOT/recovery-manifest.json" || { echo "ERROR: Jasper recovery manifest missing: $RECOVERY_BOOT/recovery-manifest.json" >&2; exit 2; }
mkdir -p "$DIST/iso/boot/recovery"
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.img" "$DIST/iso/boot/recovery/"
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.cpio" "$DIST/iso/boot/recovery/"
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.cpio.sha256" "$DIST/iso/boot/recovery/" 2>/dev/null || true
cp -f "$RECOVERY_BOOT/chimera-recovery-initramfs.img.sha256" "$DIST/iso/boot/recovery/" 2>/dev/null || true
(cd "$RECOVERY_BOOT" && sha256sum --check chimera-recovery-initramfs.cpio.sha256)
cp -f "$RECOVERY_BOOT/recovery-manifest.json" "$DIST/iso/boot/recovery/"
cp -f "$ROOT/boot/jasper/recovery.cfg" "$DIST/iso/boot/jasper/recovery.cfg"

# Stage the production Live/Installer/Recovery ring-3 payloads. Koronos only
# enters user mode when the selected GRUB entry passes exactly one
# CHIMERA_MODULE_USER_INIT_ELF module with a matching target= cmdline; staging
# the ELFs here keeps the ISO and the menu contract in sync.
printf '%s\n' '[3b/7] Stage ring-3 target inits (live, installer, recovery)'
TARGETS_OUT="$DIST/iso/boot/targets"
mkdir -p "$TARGETS_OUT"
for target in live installer recovery; do
  target_elf="$ROOT/build/koronos/x86_64/target-init-$target.elf"
  test -s "$target_elf" || { echo "ERROR: production target init missing: $target_elf (run kernel/build-koronos.sh)" >&2; exit 2; }
  grub-file --is-x86-multiboot2 "$target_elf" >/dev/null 2>&1 && true
  readelf -h "$target_elf" | grep -Eq 'Type:[[:space:]]+EXEC' || { echo "ERROR: $target_elf is not ET_EXEC" >&2; exit 2; }
  cp -f "$target_elf" "$TARGETS_OUT/"
done
for target in live installer recovery; do
  grep -q "target-init-$target.elf chimera-user-init-elf target=$target" "$ISO_ROOT/grub.cfg" || {
    echo "ERROR: GRUB menu does not reference the $target user-init module" >&2; exit 2; }
done

# Stage cross-built Linux ABI command multicall binaries for all currently
# supported Linux command ABIs. Linux ABI smoke tests do not establish Koronos syscall or kernel runtime acceptance.
printf '%s\n' '[3c] Stage Linux ABI command candidates for x86_64, i686, armel, AArch64, ARMv7, RV64, PPC64LE and s390x'
NATIVE_COMMAND_OUT="$ROOT/build/native-command-isa"
test -s "$NATIVE_COMMAND_OUT/manifest.json" || { echo "ERROR: native command ISA build manifest missing" >&2; exit 2; }
for arch in x86_64 i686 armel aarch64 armv7 riscv64 ppc64le s390x; do
  test -s "$NATIVE_COMMAND_OUT/$arch/chimera-cmd" || { echo "ERROR: Linux ABI command candidate missing for $arch" >&2; exit 2; }
  test -L "$NATIVE_COMMAND_OUT/$arch/ls" || { echo "ERROR: Linux ABI command aliases missing for $arch" >&2; exit 2; }
done
mkdir -p "$DIST/iso/system/commands/linux-abi"
cp -a "$NATIVE_COMMAND_OUT/." "$DIST/iso/system/commands/linux-abi/"
# Carry every command and ISA catalogue with explicit platform/provider metadata.
CATALOG_OUT="$DIST/iso/system/commands/catalogs"
mkdir -p "$CATALOG_OUT"
for rel in \
  system/commands/chimera-command-list.json \
  system/commands/ss64-command-catalog.json system/commands/ss64-command-catalog.ar.json \
  system/commands/native-command-candidates.json system/commands/command-runtime-capabilities.json \
  system/commands/compatibility-binary-policy.json \
  system/commands/native-provider-aliases.json \
  config/linux-command-registry.json tools/commands/os-command-runtime.json \
  ISA.csv isa/catalog.json isa/generated/universal-instruction-catalog.json \
  isa/generated/isa-encoding-registry.json data/isa/online-isa-index.json; do
  [[ -s "$ROOT/$rel" ]] && install -D -m 0644 "$ROOT/$rel" "$CATALOG_OUT/$(basename "$rel")"
done
install -D -m 0644 "$ROOT/aurora/terminals/registry.json" "$CATALOG_OUT/terminals-registry.json"
install -D -m 0644 "$ROOT/aurora/shells/registry.json" "$CATALOG_OUT/shells-registry.json"
install -D -m 0644 "$ROOT/aurora/terminals/binary-manifest.json" "$CATALOG_OUT/terminals-binary-manifest.json"
install -D -m 0644 "$ROOT/aurora/shells/binary-manifest.json" "$CATALOG_OUT/shells-binary-manifest.json"
install -D -m 0644 "$NATIVE_COMMAND_OUT/manifest.json" "$CATALOG_OUT/linux-abi-command-matrix.json"
python3 - "$NATIVE_COMMAND_OUT/manifest.json" <<'PY'
import json,sys
manifest=json.load(open(sys.argv[1],encoding="utf-8"))
expected={"x86_64","i686","armel","aarch64","armv7","riscv64","ppc64le","s390x"}
rows={row["target"]:row for row in manifest.get("targets",[])}
if set(rows)!=expected: raise SystemExit(f"wrong native command target set: {sorted(rows)}")
for arch,row in rows.items():
    if row.get("binary_status")!="cross-compiled-and-elf-machine-validated":
        raise SystemExit(f"{arch} command binary not ELF-validated: {row}")
    if row.get("runtime_status") not in {"native-linux-abi-smoke-tested","qemu-user-linux-abi-smoke-tested"}:
        raise SystemExit(f"{arch} Linux ABI smoke test missing: {row}")
if "does not validate Koronos" not in manifest.get("runtime_scope",""):
    raise SystemExit("manifest must distinguish Linux ABI smoke tests from Koronos runtime acceptance")
print("Linux ABI smoke tests passed; Koronos kernel/userspace execution remains untested.")
PY

# Stage the AI knowledge database. The kernel classifies it as
# CHIMERA_MODULE_AI_KNOWLEDGE_DB and reports its entry count on the boot trace.
printf '%s\n' '[3d/7] Stage AI knowledge database'
KB_SRC="$ROOT/config/ai/knowledge-db.json"
test -s "$KB_SRC" || { echo "ERROR: knowledge database missing: $KB_SRC (run tools/ai/knowledge_db.py build)" >&2; exit 2; }
mkdir -p "$DIST/iso/boot/ai"
cp -f "$KB_SRC" "$DIST/iso/boot/ai/knowledge-db.json"
python3 "$ROOT/tools/ai/knowledge_db.py" validate --db "$DIST/iso/boot/ai/knowledge-db.json" >/dev/null || {
  echo "ERROR: staged knowledge database failed validation" >&2; exit 2; }
sha256sum "$DIST/iso/boot/ai/knowledge-db.json" | awk '{print $1"  knowledge-db.json"}' > "$DIST/iso/boot/ai/knowledge-db.json.sha256"

# Stage the complete media / app-catalogue / documentation / CI-workflow payload
# under /payload with a manifest and per-file digests.
printf '%s\n' '[3d/7] Stage media, apps, docs and workflow payload'
python3 "$ROOT/tools/iso/stage_payload.py" --root "$ROOT" --iso "$DIST/iso" --limit-mb "${CHIMERA_PAYLOAD_LIMIT_MB:-200}"
test -s "$DIST/iso/payload/MANIFEST.json" || { echo "ERROR: payload manifest missing" >&2; exit 2; }
test -s "$DIST/iso/payload/SHA256SUMS" || { echo "ERROR: payload checksums missing" >&2; exit 2; }

printf '%s\n' '[4/7] Stage complete Aurora artwork, Init.mp4 and professional progress UI'
VISUAL_OUT="$DIST/iso/boot/visual"
mkdir -p "$VISUAL_OUT"
bash "$ROOT/tools/aurora/build-visual-assets.sh" "$ROOT/build/aurora-media"
MEDIA="$ROOT/build/aurora-media"
# Export every native Aurora SVG icon for the desktop and the installed icon theme.
ICON_OUT="$DIST/iso/desktop/aurora/icons/generated"
python3 "$ROOT/tools/aurora/export-icon-theme.py" --output "$ROOT/build/aurora-icons"
mkdir -p "$ICON_OUT" "$DIST/iso/usr/share/icons/chimera-aurora/scalable/apps"
cp -a "$ROOT/build/aurora-icons/." "$ICON_OUT/"
cp -a "$ROOT/build/aurora-icons/." "$DIST/iso/usr/share/icons/chimera-aurora/"
cp -a "$ROOT/build/aurora-icons/chimera-"*.svg "$DIST/iso/usr/share/icons/chimera-aurora/scalable/apps/"
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
# Mirror the same contract into the installed/live Aurora runtime when a rootfs is present.
RUNTIME_AURORA_ROOT="${CHIMERA_ROOTFS_DIR:-$ROOT/build/rootfs}/usr/share/chimera/aurora"
if [[ -d "$(dirname "$RUNTIME_AURORA_ROOT")" ]]; then
  mkdir -p "$RUNTIME_AURORA_ROOT"
  cp -a "$MEDIA/." "$RUNTIME_AURORA_ROOT/"
  mkdir -p "$RUNTIME_AURORA_ROOT/icons"
  cp -a "$ROOT/build/aurora-icons/." "$RUNTIME_AURORA_ROOT/icons/"
fi
printf '%s\n' '[5/7] Validate kernel-to-GRUB linkage, graphics and installation contracts'
test -s "$DIST/iso/boot/koronos/koronos.elf"
test -s "$DIST/iso/boot/spitfire/spitfire-stage2.bin"
for visual in \
  aurora-boot.png aurora-menu.png aurora-splash.png aurora-installer.png \
  aurora-recovery.png aurora-diagnostics.png aurora-live.png aurora-mobile.png \
  aurora-desktop.png Init.mp4 aurora-manifest.json state.json stages.json style.json; do
  test -s "$DIST/iso/boot/visual/$visual" || { echo "ERROR: Aurora visual asset missing: $visual" >&2; exit 2; }
done
test -s "$DIST/iso/boot/visual/aurora-media/manifest.json"
test -s "$ICON_OUT/manifest.json" || { echo "ERROR: generated Aurora icon manifest missing." >&2; exit 2; }
for stage in spitfire jasper grub koronos; do
  test -s "$DIST/iso/boot/$stage/Init.mp4" || { echo "ERROR: Init.mp4 missing from $stage stage." >&2; exit 2; }
  test -s "$DIST/iso/boot/$stage/aurora-boot.png" || { echo "ERROR: Aurora artwork missing from $stage stage." >&2; exit 2; }
  test -s "$DIST/iso/boot/$stage/boot-artwork-manifest.json" || { echo "ERROR: artwork manifest missing from $stage stage." >&2; exit 2; }
done

# Stage a real installer initramfs and the canonical installer JSON contracts.
bash "$ROOT/tools/chimera-stage-installer-media.sh" "$DIST/iso"
(cd "$DIST/iso/install/installer" && sha256sum --check installation.cpio.sha256)

grep -q 'multiboot2 /boot/koronos/koronos.elf' "$ROOT/boot/iso/grub.cfg"
grep -q 'background_image --mode stretch /boot/visual/aurora-boot.png' "$ROOT/boot/iso/grub.cfg"
grep -q '"native_execution_order"' "$DIST/iso/boot/chimera/manifests/boot-execution-order.json"

test -s "$DIST/iso/boot/live/chimera-live-initramfs.img" || { echo "Live initramfs missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/live/chimera-live-initramfs.cpio" || { echo "Raw live CPIO VFS archive missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/live/live-manifest.json" || { echo "Live manifest missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/loader-menu.cfg" || { echo "Universal Gates loader menu missing from ISO staging tree." >&2; exit 1; }
grep -Fq "target-init-live.elf chimera-user-init-elf target=live" "$DIST/iso/boot/loader-menu.cfg" || {
  echo "Universal Gates loader menu does not select the native Live init ELF" >&2; exit 1;
}
grep -Fq "target-init-recovery.elf chimera-user-init-elf target=recovery" "$DIST/iso/boot/loader-menu.cfg" || {
  echo "Universal Gates loader menu does not select the native Recovery init ELF" >&2; exit 1;
}
test -s "$DIST/iso/boot/recovery/chimera-recovery-initramfs.img" || { echo "Recovery initramfs missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/recovery/chimera-recovery-initramfs.cpio" || { echo "Recovery CPIO VFS archive missing from ISO staging tree." >&2; exit 1; }
test -s "$DIST/iso/boot/recovery/recovery-manifest.json" || { echo "Recovery manifest missing from ISO staging tree." >&2; exit 1; }
grep -q '/boot/live/chimera-live-initramfs.img' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/live/chimera-live-initramfs.cpio' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/live/live-manifest.json' "$ROOT/boot/jasper/live.cfg"
grep -q '/boot/recovery/chimera-recovery-initramfs.img' "$ROOT/boot/jasper/recovery.cfg"
grep -q '/boot/recovery/chimera-recovery-initramfs.cpio' "$ROOT/boot/jasper/recovery.cfg"
grep -q 'Recovery Terminal' "$ROOT/boot/jasper/recovery.cfg"

for contract in \
  "$DIST/iso/install/installer/installation.img" \
  "$DIST/iso/install/installer/installation.cpio" \
  "$DIST/iso/install/installer/installation.cpio.sha256" \
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
# grub-mkrescue accepts its own options before the source tree. Do not pass
# genisoimage/mkisofs flags such as -iso-level directly: grub-mkrescue forwards
# them to xorriso, where they are rejected as unknown commands. Let xorriso use
# its native defaults for a hybrid BIOS/UEFI image.
grub-mkrescue -o "$DIST/output.iso" "$DIST/iso"
test -s "$DIST/output.iso"
sha256sum "$DIST/output.iso" | tee "$DIST/output.iso.sha256"

printf '%s\n' '[7/7] Inspect El Torito boot records'
xorriso -indev "$DIST/output.iso" -report_el_torito plain -report_system_area plain | tee "$DIST/ISO-BOOT-REPORT.txt"
printf 'ISO: %s\nKoronos: %s\nSpit Fire: %s\nAurora background: %s\nBoot video: %s\nRecovery terminal: %s\n' \
  "$DIST/output.iso" "$DIST/iso/boot/koronos/koronos.elf" "$DIST/iso/boot/spitfire/spitfire-stage2.bin" \
  "$DIST/iso/boot/visual/aurora-boot.png" "$DIST/iso/boot/visual/Init.mp4" \
  "$DIST/iso/boot/recovery/chimera-recovery-initramfs.img"
