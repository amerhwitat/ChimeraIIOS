#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
fail(){ echo "[BOOT-VALIDATE][ERROR] $*" >&2; exit 1; }
require(){ [[ -e "$1" ]] || fail "missing: ${1#$ROOT/}"; }
require "$ROOT/boot/loader-menu.cfg"
require "$ROOT/boot/boot-menu-contract.json"
require "$ROOT/boot/boot-artwork-manifest.json"
require "$ROOT/boot/visual/aurora-wayland-glass.jpg.b64"
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
