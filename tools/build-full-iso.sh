#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/full"
ISO_DIR="$ROOT/build/iso"
mkdir -p "$BUILD" "$ISO_DIR"
DISK_MANAGER="$ROOT/tools/disk-space-manager.sh"
if [[ -x "$DISK_MANAGER" ]]; then
  CHIMERA_ROOT="$ROOT" CHIMERA_EXPECTED_BUILD_GB="${CHIMERA_EXPECTED_BUILD_GB:-80}" CHIMERA_MIN_FREE_GB="${CHIMERA_MIN_FREE_GB:-100}" CHIMERA_DISK_RESERVE_GB="${CHIMERA_DISK_RESERVE_GB:-20}" "$DISK_MANAGER"
fi
FOREIGN="$ROOT/build/foreign"
MOBILE="$ROOT/build/mobile"
DRIVERS="$ROOT/build/drivers"

cmake -S "$ROOT" -B "$BUILD/cmake" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD/cmake" --target all koronos-x86_64 --parallel "${CHIMERA_JOBS:-2}"

for tool in build-desktop-binaries.sh build-koronos-targets.sh build-toolchain-bundle.sh build-network-toolkit.sh fetch-driver-payloads.sh fetch-foreign-runtimes.sh build-mobile-edition.sh build-compatibility-binaries.sh; do
  chmod +x "$ROOT/tools/$tool"
done
"$ROOT/tools/build-network-toolkit.sh"
"$ROOT/tools/build-toolchain-bundle.sh"
"$ROOT/tools/fetch-driver-payloads.sh"
"$ROOT/tools/build-koronos-targets.sh"
"$ROOT/tools/fetch-foreign-runtimes.sh"
"$ROOT/tools/build-compatibility-binaries.sh"
"$ROOT/tools/build-mobile-edition.sh"
"$ROOT/tools/build-desktop-binaries.sh"

if command -v javac >/dev/null 2>&1 && command -v jar >/dev/null 2>&1; then bash "$ROOT/sdk/java/build.sh"; fi
python3 -m compileall -q "$ROOT/sdk/python/chimera_sdk"
if [[ -x "$DISK_MANAGER" ]]; then CHIMERA_ROOT="$ROOT" "$DISK_MANAGER"; fi

KERNEL="$(find "$BUILD/cmake" "$ROOT/build" "$ROOT/kernel" -type f \( -name "koronos*.elf" -o -name "kernel.bin" -o -name "koronos.elf" \) 2>/dev/null | head -n1 || true)"
SPIT_IMG="${CHIMERA_SPITFIRE_IMG:-}"
if [[ -z "$SPIT_IMG" ]]; then SPIT_IMG="$(find "$ROOT" -type f \( -iname "*spit*fire*.img" -o -iname "spitfire*.img" \) 2>/dev/null | head -n1 || true)"; fi

BASE="${CHIMERA_BASE_ISO:-}"
for c in "$ROOT/chimera-ii-os.iso" "$ROOT/releases/chimera-ii-os.iso"; do
  [[ -z "$BASE" && -f "$c" ]] && BASE="$c"
done
if [[ -z "$BASE" && "${CHIMERA_FETCH_RELEASE:-0}" == "1" ]] && command -v gh >/dev/null 2>&1; then
  mkdir -p "$ROOT/releases"
  CHIMERA_RELEASE_TAG="${CHIMERA_RELEASE_TAG:-latest}" "$ROOT/tools/fetch-release-media.sh" "$ROOT/releases"
  [[ -f "$ROOT/releases/chimera-ii-os.iso" ]] && BASE="$ROOT/releases/chimera-ii-os.iso"
  [[ -z "$SPIT_IMG" ]] && SPIT_IMG="$(find "$ROOT/releases" -type f -iname "*spit*fire*.img" | head -n1 || true)"
fi
if [[ -z "$BASE" && -n "${CHIMERA_BASE_ISO_URL:-}" ]]; then
  curl -fL --retry 3 "$CHIMERA_BASE_ISO_URL" -o "$BUILD/base.iso"
  BASE="$BUILD/base.iso"
fi

STAGE="$BUILD/inject"
if [[ -x "$DISK_MANAGER" ]]; then CHIMERA_ROOT="$ROOT" CHIMERA_EXPECTED_BUILD_GB="${CHIMERA_EXPECTED_BUILD_GB:-100}" "$DISK_MANAGER"; fi
rm -rf "$STAGE"
mkdir -p "$STAGE/boot" "$STAGE/install" "$STAGE/system" "$STAGE/sdk" "$STAGE/desktop"
[[ -n "$KERNEL" && -f "$KERNEL" ]] && cp "$KERNEL" "$STAGE/boot/koronos.elf"
[[ -n "$SPIT_IMG" && -f "$SPIT_IMG" ]] && cp "$SPIT_IMG" "$STAGE/boot/spitfire.img"
cp -a "$ROOT/installer" "$STAGE/install/"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
cp -a "$ROOT/build/desktop/." "$STAGE/desktop/"
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/system/security" "$STAGE/system/security"
cp -a "$ROOT/tools/initialize-accounts.sh" "$STAGE/install/initialize-accounts.sh"
cp -a "$ROOT/boot" "$STAGE/system/boot"
cp -a "$ROOT/sdk" "$STAGE/install/sdk-source"
cp -a "$ROOT/sdk" "$STAGE/sdk"

for source_dir in kernel src include database cmake tools boot installer userland desktop services iso; do
  if [[ -d "$ROOT/$source_dir" ]]; then
    mkdir -p "$STAGE/source"
    cp -a "$ROOT/$source_dir" "$STAGE/source/"
  fi
done

mkdir -p "$STAGE/build-artifacts" "$STAGE/compat" "$STAGE/mobile" "$STAGE/drivers" "$STAGE/toolchains"   "$STAGE/opt/chimera/toolchains" "$STAGE/network-tools" "$STAGE/opt/chimera/network-tools"
cp -a "$ROOT/build/desktop" "$STAGE/build-artifacts/" 2>/dev/null || true
cp -a "$ROOT/build/koronos/ports" "$STAGE/build-artifacts/" 2>/dev/null || true
cp -a "$BUILD/cmake" "$STAGE/build-artifacts/cmake" 2>/dev/null || true
cp -a "$FOREIGN" "$STAGE/compat/foreign-runtime" 2>/dev/null || true
cp -a "$MOBILE" "$STAGE/mobile/" 2>/dev/null || true
cp -a "$DRIVERS" "$STAGE/drivers/" 2>/dev/null || true
cp -a "$ROOT/build/toolchains/." "$STAGE/opt/chimera/toolchains/" 2>/dev/null || true
cp -a "$ROOT/build/toolchains" "$STAGE/toolchains/" 2>/dev/null || true
cp -a "$ROOT/build/network-tools/." "$STAGE/opt/chimera/network-tools/" 2>/dev/null || true
cp -a "$ROOT/build/network-tools" "$STAGE/network-tools/" 2>/dev/null || true
cp -a "$ROOT/network" "$STAGE/system/network" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/route-manager.desktop.json" "$STAGE/system/desktop/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/networking_panel.json" "$STAGE/system/desktop/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/wallpaper-service.json" "$STAGE/system/desktop/" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/wallpaper-service.py" "$STAGE/system/desktop/" 2>/dev/null || true
cp -a "$ROOT/services/learning" "$STAGE/system/services/learning" 2>/dev/null || true
cp -a "$ROOT/services/network" "$STAGE/system/services/network" 2>/dev/null || true
cp -a "$ROOT/desktop/aurora/network-discovery.desktop.json" "$STAGE/system/desktop/" 2>/dev/null || true

mkdir -p "$STAGE/install/sdk"
for d in include python csharp objective-c java manuals examples toolchains bin; do
  [[ -e "$ROOT/sdk/$d" ]] && cp -a "$ROOT/sdk/$d" "$STAGE/install/sdk/"
done
for f in runtime-profiles.json manifest.json SDK_BUILD_MANIFEST.json; do
  [[ -f "$ROOT/sdk/$f" ]] && cp "$ROOT/sdk/$f" "$STAGE/install/sdk/"
done
[[ -f "$ROOT/sdk/manuals/TOOLCHAIN_SETUP.md" ]] && cp "$ROOT/sdk/manuals/TOOLCHAIN_SETUP.md" "$STAGE/install/sdk/manuals/"
if [[ -f "$ROOT/sdk/java/chimera-sdk.jar" ]]; then cp "$ROOT/sdk/java/chimera-sdk.jar" "$STAGE/install/sdk/"; fi
if [[ -n "${CHIMERA_AURORA_BACKGROUND:-}" && -f "$CHIMERA_AURORA_BACKGROUND" ]]; then
  mkdir -p "$STAGE/install/assets/aurora"
  cp "$CHIMERA_AURORA_BACKGROUND" "$STAGE/install/assets/aurora/Aurora-Wayland-Glass-Desktop.png"
fi

FINAL="$ISO_DIR/chimera-ii-os.iso"
if [[ -x "$DISK_MANAGER" ]]; then CHIMERA_ROOT="$ROOT" CHIMERA_EXPECTED_BUILD_GB="${CHIMERA_EXPECTED_BUILD_GB:-100}" "$DISK_MANAGER"; fi
if [[ -n "$BASE" && -f "$BASE" ]] && command -v xorriso >/dev/null 2>&1; then
  # xorriso refuses a non-empty existing outdev when indev and outdev differ.
  # Delete the previous output before opening the base image. If BASE happens
  # to point at FINAL, first preserve it under a distinct path.
  if [[ "$(readlink -f "$BASE" 2>/dev/null || true)" == "$(readlink -f "$FINAL" 2>/dev/null || true)" ]]; then
    cp --reflink=auto "$BASE" "$BUILD/base-for-inject.iso"
    BASE="$BUILD/base-for-inject.iso"
  fi
  rm -f "$FINAL"
  xorriso -indev "$BASE" -outdev "$FINAL" -map "$STAGE" /chimera -commit -end
else
  CHIMERA_KERNEL="$KERNEL" CHIMERA_OUTPUT_ISO="$FINAL" "$ROOT/iso/chimera-live-iso.sh"
fi

[[ -s "$FINAL" ]] || { echo "ERROR: ISO was not produced: $FINAL" >&2; exit 1; }
cp "$FINAL" "$ROOT/chimera-ii-os.iso"
sha256sum "$FINAL" | tee "$FINAL.sha256"
echo "Built $FINAL"
