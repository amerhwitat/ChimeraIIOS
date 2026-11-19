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
ROOT_DISCOVERY="$ROOT/tools/boot/chimera-root-discovery.sh"
LIVE_BUILD="$ROOT/tools/build-live-boot-binaries.sh"
INSTALLER_STAGE="$ROOT/tools/chimera-stage-installer-media.sh"

grep -q '/install/installer/installation.img' "$JASPER"
grep -q '/install/installer/installation-manifest.json' "$JASPER"
grep -q 'installation.img' "$BUILD"
grep -q 'installation-manifest.json' "$BUILD"
grep -q 'installer-initrd.img' "$BUILD"
grep -q 'live-manifest.json' "$ISO"
grep -q 'chimera-stage-installer-media.sh' "$ISO"
grep -q 'installation.img' "$ISO"
grep -q 'chimera-root-discovery.sh' "$BUILD"
grep -q 'chimera-root-discovery.sh' "$LIVE_BUILD"
grep -q 'chimera-root-discovery.sh' "$INSTALLER_STAGE"
grep -q 'chimera-root-discovery.sh recovery' "$LIVE_BUILD"
grep -q 'chimera-root-discovery.sh live' "$LIVE_BUILD"
grep -q 'chimera-root-discovery.sh installer' "$INSTALLER_STAGE"
grep -q 'runtime_root "initramfs"' "$ROOT_DISCOVERY"
grep -q 'mount -o ro' "$ROOT_DISCOVERY"
grep -q 'fallback "no-validated-installed-root"' "$ROOT_DISCOVERY"
sh -n "$ROOT_DISCOVERY"
grep -Eq '(-rockridge[[:space:]]+on|^[[:space:]]+-R([[:space:]]|$))' "$ISO"

bash -n "$BUILD"
bash -n "$ISO"
bash -n "$LIVE_BUILD"
bash -n "$INSTALLER_STAGE"
echo "installation media contract: OK"
echo "installation media contract: OK"
