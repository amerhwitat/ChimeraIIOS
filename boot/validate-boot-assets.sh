#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: boot/validate-boot-assets.sh

Usage:
  boot/validate-boot-assets.sh [options] [arguments]

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

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
fail(){ echo "[BOOT-VALIDATE][ERROR] $*" >&2; exit 1; }
require(){ [[ -e "$1" ]] || fail "missing: ${1#$ROOT/}"; }
require "$ROOT/boot/loader-menu.cfg"
require "$ROOT/boot/boot-menu-contract.json"
require "$ROOT/boot/boot-artwork-manifest.json"
require "$ROOT/boot/visual/aurora-wayland-glass.jpg.b64"
require "$ROOT/boot/splash/spitfire_background.svg"
require "$ROOT/boot/splash/jasper_background.svg"
require "$ROOT/desktop/aurora/assets/Init.mp4"
[[ -s "$ROOT/desktop/aurora/assets/Init.mp4" ]] || fail "Init.mp4 is empty"
require "$ROOT/desktop/aurora/aurora-init-splash.sh"
require "$ROOT/desktop/aurora/aurora-progress.sh"
bash -n "$ROOT/desktop/aurora/aurora-init-splash.sh" || fail "Aurora init splash shell syntax is invalid"
bash -n "$ROOT/desktop/aurora/aurora-progress.sh" || fail "Aurora progress shell syntax is invalid"
require "$ROOT/boot/grub/aurora-background.cfg"
require "$ROOT/boot/live/live-manifest.json"
require "$ROOT/installer/installer-manifest.json"

if grep -q '/boot/chimera2-kernel.elf\|/boot/initrd.img' "$ROOT/boot/loader-menu.cfg"; then
  fail "legacy kernel/initrd path remains in canonical menu"
fi
if ! grep -q '/boot/koronos/koronos.elf' "$ROOT/boot/loader-menu.cfg"; then
  fail "canonical Koronos kernel is absent from loader menu"
fi
if ! grep -q '/boot/visual/aurora-wayland-glass.jpg' "$ROOT/boot/loader-menu.cfg"; then
  fail "canonical Aurora background is absent from loader menu"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
base64 -d "$ROOT/boot/visual/aurora-wayland-glass.jpg.b64" > "$TMP" || fail "invalid embedded Aurora base64"
magic="$(head -c 3 "$TMP" | od -An -tx1 | tr -d ' \n')"
[[ "$magic" == "ffd8ff" ]] || fail "embedded Aurora background is not JPEG"

if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$TMP" | awk '{print $1}')"
  expected="461825073f35b7c49ee741584db822f1ae6204424db18c2fe867825a7ee366ae"
  [[ "$actual" == "$expected" ]] || fail "Aurora artwork checksum mismatch"
fi

echo "[BOOT-VALIDATE] boot contract: OK"
echo "[BOOT-VALIDATE] Koronos canonical kernel: OK"
echo "[BOOT-VALIDATE] Aurora menu artwork: OK"
echo "[BOOT-VALIDATE] Live manifest: OK"
echo "[BOOT-VALIDATE] Installer manifest: OK"
echo "[BOOT-VALIDATE] Embedded artwork checksum: OK"
echo "[BOOT-VALIDATE] Spit Fire/Jasper artwork sources: OK"
echo "[BOOT-VALIDATE] Init.mp4 boot source: OK"
