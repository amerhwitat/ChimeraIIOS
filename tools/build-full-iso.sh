#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/full"
ISO_DIR="$ROOT/build/iso"
mkdir -p "$BUILD" "$ISO_DIR"
FOREIGN="$ROOT/build/foreign"
MOBILE="$ROOT/build/mobile"
cmake -S "$ROOT" -B "$BUILD/cmake" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD/cmake" --target all koronos-x86_64 --parallel "${CHIMERA_JOBS:-2}"
chmod +x "$ROOT/tools/build-desktop-binaries.sh"
chmod +x "$ROOT/tools/build-koronos-targets.sh"
"$ROOT/tools/build-koronos-targets.sh"
chmod +x "$ROOT/tools/fetch-foreign-runtimes.sh" "$ROOT/tools/build-mobile-edition.sh" "$ROOT/tools/build-compatibility-binaries.sh"
"$ROOT/tools/fetch-foreign-runtimes.sh"
"$ROOT/tools/build-compatibility-binaries.sh"
"$ROOT/tools/build-mobile-edition.sh"
"$ROOT/tools/build-desktop-binaries.sh"
if command -v javac >/dev/null 2>&1 && command -v jar >/dev/null 2>&1; then bash "$ROOT/sdk/java/build.sh"; fi
python3 -m compileall -q "$ROOT/sdk/python/chimera_sdk"
KERNEL="$(find "$BUILD/cmake" "$ROOT/build" "$ROOT/kernel" -type f \( -name "koronos*.elf" -o -name "kernel.bin" -o -name "koronos.elf" \) 2>/dev/null | head -n1 || true)"
SPIT_IMG="${CHIMERA_SPITFIRE_IMG:-}"
if [[ -z "$SPIT_IMG" ]]; then SPIT_IMG="$(find "$ROOT" -type f \( -iname "*spit*fire*.img" -o -iname "spitfire*.img" \) 2>/dev/null | head -n1 || true)"; fi
BASE="${CHIMERA_BASE_ISO:-}"
for c in "$ROOT/chimera-ii-os.iso" "$ROOT/releases/chimera-ii-os.iso"; do [[ -z "$BASE" && -f "$c" ]] && BASE="$c"; done
if [[ -z "$BASE" && "${CHIMERA_FETCH_RELEASE:-0}" == "1" ]] && command -v gh >/dev/null 2>&1; then
  mkdir -p "$ROOT/releases"
  CHIMERA_RELEASE_TAG="${CHIMERA_RELEASE_TAG:-latest}" "$ROOT/tools/fetch-release-media.sh" "$ROOT/releases"
  [[ -f "$ROOT/releases/chimera-ii-os.iso" ]] && BASE="$ROOT/releases/chimera-ii-os.iso"
  [[ -z "$SPIT_IMG" ]] && SPIT_IMG="$(find "$ROOT/releases" -type f -iname "*spit*fire*.img" | head -n1 || true)"
fi
if [[ -z "$BASE" && -n "${CHIMERA_BASE_ISO_URL:-}" ]]; then curl -fL "$CHIMERA_BASE_ISO_URL" -o "$BUILD/base.iso"; BASE="$BUILD/base.iso"; fi
STAGE="$BUILD/inject"; rm -rf "$STAGE"; mkdir -p "$STAGE/boot" "$STAGE/install" "$STAGE/system" "$STAGE/sdk" "$STAGE/desktop"
[[ -n "$KERNEL" && -f "$KERNEL" ]] && cp "$KERNEL" "$STAGE/boot/koronos.elf"
[[ -n "$SPIT_IMG" && -f "$SPIT_IMG" ]] && cp "$SPIT_IMG" "$STAGE/boot/spitfire.img"
cp -a "$ROOT/installer" "$STAGE/install/"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
cp -a "$ROOT/build/desktop/." "$STAGE/desktop/"
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/boot" "$STAGE/system/boot"
cp -a "$ROOT/sdk" "$STAGE/install/sdk-source"
cp -a "$ROOT/sdk" "$STAGE/sdk"
# Preserve the complete source tree on the developer/recovery ISO.
for source_dir in kernel src include database cmake tools boot installer userland desktop services iso; do
  if [[ -d "$ROOT/$source_dir" ]]; then
    mkdir -p "$STAGE/source"
    cp -a "$ROOT/$source_dir" "$STAGE/source/"
  fi
done
mkdir -p "$STAGE/build-artifacts" "$STAGE/compat" "$STAGE/mobile"
cp -a "$ROOT/build/desktop" "$STAGE/build-artifacts/" 2>/dev/null || true
cp -a "$ROOT/build/koronos/ports" "$STAGE/build-artifacts/" 2>/dev/null || true
cp -a "$BUILD/cmake" "$STAGE/build-artifacts/cmake" 2>/dev/null || true
cp -a "$FOREIGN" "$STAGE/compat/foreign-runtime" 2>/dev/null || true
cp -a "$MOBILE" "$STAGE/mobile/" 2>/dev/null || true
mkdir -p "$STAGE/install/sdk"
cp -a "$ROOT/sdk/include" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/python" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/csharp" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/objective-c" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/java" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/manuals" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/examples" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/toolchains" "$STAGE/install/sdk/"
cp -a "$ROOT/sdk/bin" "$STAGE/install/sdk/"
cp "$ROOT/sdk/runtime-profiles.json" "$STAGE/install/sdk/"
cp "$ROOT/sdk/manifest.json" "$STAGE/install/sdk/"
cp "$ROOT/sdk/SDK_BUILD_MANIFEST.json" "$STAGE/install/sdk/"
cp "$ROOT/sdk/manuals/TOOLCHAIN_SETUP.md" "$STAGE/install/sdk/manuals/"
if [[ -f "$ROOT/sdk/java/chimera-sdk.jar" ]]; then cp "$ROOT/sdk/java/chimera-sdk.jar" "$STAGE/install/sdk/"; fi
if [[ -n "${CHIMERA_AURORA_BACKGROUND:-}" && -f "$CHIMERA_AURORA_BACKGROUND" ]]; then mkdir -p "$STAGE/install/assets/aurora"; cp "$CHIMERA_AURORA_BACKGROUND" "$STAGE/install/assets/aurora/Aurora-Wayland-Glass-Desktop.png"; fi
FINAL="$ISO_DIR/chimera-ii-os.iso"
if [[ -n "$BASE" && -f "$BASE" ]] && command -v xorriso >/dev/null 2>&1; then xorriso -indev "$BASE" -outdev "$FINAL" -map "$STAGE" /chimera -commit -end; else CHIMERA_KERNEL="$KERNEL" CHIMERA_OUTPUT_ISO="$FINAL" "$ROOT/iso/chimera-live-iso.sh"; fi
cp "$FINAL" "$ROOT/chimera-ii-os.iso"
sha256sum "$FINAL" | tee "$FINAL.sha256"
echo "Built $FINAL"
