#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tests/image/test_installation_media_contract.sh

Usage:
  tests/image/test_installation_media_contract.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
BUILD="$ROOT/build-chimera-iso.sh"
JASPER="$ROOT/boot/jasper/install.cfg"
ISO="$ROOT/iso/chimera-live-iso.sh"
GRUB="$ROOT/boot/iso/grub.cfg"
RECOVERY="$ROOT/boot/jasper/recovery.cfg"
KERNEL_BUILD="$ROOT/kernel/build-koronos.sh"
TARGET_LAUNCH="$ROOT/kernel/core/target_launch.cpp"
NEWC="$ROOT/kernel/core/initramfs_newc.cpp"
RAMFS="$ROOT/kernel/core/initramfs_fs.cpp"
LIVE_BUILD="$ROOT/tools/build-live-boot-binaries.sh"
INSTALLER_STAGE="$ROOT/tools/chimera-stage-installer-media.sh"

grep -q '/install/installer/installation.cpio' "$JASPER"
grep -q '/boot/live/chimera-live-initramfs.cpio' "$GRUB"
grep -q '/boot/recovery/chimera-recovery-initramfs.cpio' "$GRUB"
grep -q '/boot/recovery/chimera-recovery-initramfs.cpio' "$RECOVERY"
grep -q 'chimera-live-initramfs.cpio' "$LIVE_BUILD"
grep -q 'chimera-recovery-initramfs.cpio' "$LIVE_BUILD"
grep -q 'installation.cpio' "$BUILD"
grep -q 'installation.cpio' "$INSTALLER_STAGE"
grep -q 'koronos_initramfs_mount' "$TARGET_LAUNCH"
grep -q 'initramfs_newc' "$KERNEL_BUILD"
grep -q 'initramfs_fs' "$KERNEL_BUILD"
grep -q 'koronos_newc_walk' "$NEWC"
grep -q 'koronos_initramfs_lookup' "$RAMFS"
grep -q 'installation.cpio' "$JASPER"
grep -q 'installation.cpio' "$ROOT/install/installation-manifest.json"
grep -q 'chimera-live-initramfs.cpio.sha256' "$LIVE_BUILD"
grep -q 'chimera-recovery-initramfs.cpio.sha256' "$LIVE_BUILD"
grep -q 'chimera-live-initramfs.cpio.sha256' "$BUILD"
grep -q 'chimera-recovery-initramfs.cpio.sha256' "$BUILD"
grep -q 'installation.cpio' "$JASPER"
grep -q '/install/installer/installation-manifest.json' "$JASPER"
grep -q 'installation.img' "$BUILD"
grep -q 'installation-manifest.json' "$BUILD"
grep -q 'installer-initrd.img' "$BUILD"
grep -q 'live-manifest.json' "$ISO"
grep -q 'chimera-stage-installer-media.sh' "$ISO"
grep -q 'installation.img' "$ISO"
grep -Eq '(-rockridge[[:space:]]+on|^[[:space:]]+-R([[:space:]]|$))' "$ISO"

bash -n "$BUILD"
bash -n "$ISO"
bash -n "$LIVE_BUILD"
bash -n "$INSTALLER_STAGE"
echo "installation media contract: OK"
