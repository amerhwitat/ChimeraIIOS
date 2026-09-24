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
mkdir -p "$STAGE/boot/koronos" "$STAGE/boot/live" "$STAGE/boot/jasper" "$STAGE/boot/spitfire" "$STAGE/boot/installation" "$STAGE/boot/recovery" "$STAGE/boot/diagnostics" "$STAGE/install" "$STAGE/system" "$STAGE/desktop" "$STAGE/compat" "$STAGE/mobile" "$STAGE/drivers" "$STAGE/toolchains" "$STAGE/opt/chimera/toolchains" "$STAGE/network-tools" "$STAGE/opt/chimera/network-tools" "$(dirname "$OUT")"
copy_if_distinct() {
  local src="$1" dst="$2"
  if [[ -f "$src" && -f "$dst" ]] && [[ "$(readlink -f "$src")" == "$(readlink -f "$dst")" ]]; then
    return 0
  fi
  cp -f "$src" "$dst"
}
if [[ -n "${CHIMERA_KERNEL:-}" && -f "$CHIMERA_KERNEL" ]]; then
  copy_if_distinct "$CHIMERA_KERNEL" "$STAGE/boot/koronos/koronos.elf"
fi
cp "$ROOT/boot/livecd/live-manifest.json" "$STAGE/boot/"
cp -a "$ROOT/installer" "$STAGE/install/installer-source"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
if [[ -d "$ROOT/build/desktop" ]]; then cp -a "$ROOT/build/desktop/." "$STAGE/desktop/"; fi
if [[ -d "$ROOT/build/foreign" ]]; then cp -a "$ROOT/build/foreign/." "$STAGE/compat/"; fi
if [[ -d "$ROOT/build/mobile" ]]; then cp -a "$ROOT/build/mobile/." "$STAGE/mobile/"; fi
if [[ -d "$ROOT/build/drivers" ]]; then cp -a "$ROOT/build/drivers/." "$STAGE/drivers/"; fi
if [[ -d "$ROOT/build/network-tools" ]]; then cp -a "$ROOT/build/network-tools/." "$STAGE/opt/chimera/network-tools/"; cp -a "$ROOT/build/network-tools" "$STAGE/network-tools/"; fi
if [[ -d "$ROOT/build/toolchains" ]]; then cp -a "$ROOT/build/toolchains/." "$STAGE/opt/chimera/toolchains/"; cp -a "$ROOT/build/toolchains/." "$STAGE/toolchains/"; fi
if [[ -d "$ROOT/services/learning" ]]; then cp -a "$ROOT/services/learning" "$STAGE/system/services/learning"; fi
if [[ -d "$ROOT/services/network" ]]; then cp -a "$ROOT/services/network" "$STAGE/system/services/network"; fi
for x in route-manager.desktop.json networking_panel.json wallpaper-service.json wallpaper-service.py; do [[ -f "$ROOT/desktop/aurora/$x" ]] && cp "$ROOT/desktop/aurora/$x" "$STAGE/system/desktop/"; done
[[ -d "$ROOT/network" ]] && cp -a "$ROOT/network" "$STAGE/system/network"
if [[ -f "$ROOT/desktop/aurora/network-discovery.desktop.json" ]]; then cp "$ROOT/desktop/aurora/network-discovery.desktop.json" "$STAGE/system/desktop/"; fi
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/boot" "$STAGE/system/boot"
if [[ -d "$ROOT/build/live-boot/boot" ]]; then cp -a "$ROOT/build/live-boot/boot/." "$STAGE/boot/"; fi
cp -a "$ROOT/boot/jasper/." "$STAGE/boot/jasper/"
cp -a "$ROOT/boot/spitfire/spitfire-menu.cfg" "$STAGE/boot/spitfire/"
cp -a "$ROOT/boot/installation/menu.cfg" "$STAGE/boot/installation/"
cp -a "$ROOT/boot/recovery/." "$STAGE/boot/recovery/"
cp -a "$ROOT/boot/diagnostics/." "$STAGE/boot/diagnostics/"
cp -a "$ROOT/boot/boot-menu-contract.json" "$STAGE/boot/"

install_iso_dependencies() {
  local missing=()
  command -v grub-mkrescue >/dev/null 2>&1 || missing+=(grub-mkrescue)
  command -v mformat >/dev/null 2>&1 || missing+=(mtools)
  command -v xorriso >/dev/null 2>&1 || missing+=(xorriso)

  if ((${#missing[@]} == 0)); then
    return 0
  fi

  if [[ "${CHIMERA_AUTO_INSTALL_DEPS:-1}" != "1" ]]; then
    echo "Missing ISO build dependencies: ${missing[*]}" >&2
    echo "Install mtools (provides mformat), GRUB rescue tools, and xorriso, or set CHIMERA_AUTO_INSTALL_DEPS=1." >&2
    exit 2
  fi

  if command -v apt-get >/dev/null 2>&1; then
    local packages=(mtools xorriso grub-common grub-pc-bin grub-efi-amd64-bin)
    if command -v sudo >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y "${packages[@]}"
    elif [[ "$(id -u)" -eq 0 ]]; then
      apt-get update
      apt-get install -y "${packages[@]}"
    else
      echo "Missing ISO build dependencies: ${missing[*]}" >&2
      echo "Run: sudo apt-get update && sudo apt-get install -y mtools xorriso grub-common grub-pc-bin grub-efi-amd64-bin" >&2
      exit 2
    fi
  else
    echo "Missing ISO build dependencies: ${missing[*]}" >&2
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
cp "$ROOT/boot/iso/grub.cfg" "$STAGE/boot/grub/grub.cfg"
rm -f "$OUT"
grub-mkrescue -o "$OUT" "$STAGE"
sha256sum "$OUT" > "$OUT.sha256"
