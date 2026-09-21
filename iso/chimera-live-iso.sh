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
install_iso_dependencies() {
  local missing=()
  command -v grub-mkrescue >/dev/null 2>&1 || missing+=(grub-mkrescue)
  command -v mformat >/dev/null 2>&1 || missing+=(mtools)
  command -v xorriso >/dev/null 2>&1 || missing+=(xorriso)

  if ((${#missing[@]} == 0)); then
    return 0
  fi

  if [[ "\${CHIMERA_AUTO_INSTALL_DEPS:-1}" != "1" ]]; then
    echo "Missing ISO build dependencies: \${missing[*]}" >&2
    echo "Install mtools (provides mformat), GRUB rescue tools, and xorriso, or set CHIMERA_AUTO_INSTALL_DEPS=1." >&2
    exit 2
  fi

  if command -v apt-get >/dev/null 2>&1; then
    local packages=(mtools xorriso grub-common grub-pc-bin grub-efi-amd64-bin)
    if command -v sudo >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y "\${packages[@]}"
    elif [[ "\$(id -u)" -eq 0 ]]; then
      apt-get update
      apt-get install -y "\${packages[@]}"
    else
      echo "Missing ISO build dependencies: \${missing[*]}" >&2
      echo "Run: sudo apt-get update && sudo apt-get install -y mtools xorriso grub-common grub-pc-bin grub-efi-amd64-bin" >&2
      exit 2
    fi
  else
    echo "Missing ISO build dependencies: \${missing[*]}" >&2
    echo "This host is not Debian/Ubuntu based; install mtools (mformat), xorriso, and GRUB rescue tools using the host package manager." >&2
    exit 2
  fi

  command -v grub-mkrescue >/dev/null 2>&1 || { echo "grub-mkrescue is still unavailable after dependency installation" >&2; exit 2; }
  command -v mformat >/dev/null 2>&1 || { echo "mtools/mformat is still unavailable after dependency installation" >&2; exit 2; }
  command -v xorriso >/dev/null 2>&1 || { echo "xorriso is still unavailable after dependency installation" >&2; exit 2; }
}
install_iso_dependencies
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
