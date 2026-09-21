#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build/full"
ISO_DIR="$ROOT/build/iso"
mkdir -p "$BUILD" "$ISO_DIR"
cmake -S "$ROOT" -B "$BUILD/cmake" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD/cmake" --parallel "${CHIMERA_JOBS:-2}"
KERNEL="$(find "$BUILD/cmake" "$ROOT/build" "$ROOT/kernel" -type f \( -name "koronos*.elf" -o -name "kernel.bin" -o -name "koronos.elf" \) 2>/dev/null | head -n1 || true)"
SPIT_IMG="${CHIMERA_SPITFIRE_IMG:-}"
if [[ -z "$SPIT_IMG" ]]; then SPIT_IMG="$(find "$ROOT" -type f \( -iname "*spit*fire*.img" -o -iname "spitfire*.img" \) 2>/dev/null | head -n1 || true)"; fi
BASE="${CHIMERA_BASE_ISO:-}"
for c in "$ROOT/chimera-ii-os.iso" "$ROOT/releases/chimera-ii-os.iso"; do [[ -z "$BASE" && -f "$c" ]] && BASE="$c"; done
if [[ -z "$BASE" && -n "${CHIMERA_BASE_ISO_URL:-}" ]]; then curl -fL "$CHIMERA_BASE_ISO_URL" -o "$BUILD/base.iso"; BASE="$BUILD/base.iso"; fi
STAGE="$BUILD/inject"; rm -rf "$STAGE"; mkdir -p "$STAGE/boot" "$STAGE/install" "$STAGE/system"
[[ -n "$KERNEL" && -f "$KERNEL" ]] && cp "$KERNEL" "$STAGE/boot/koronos.elf"
[[ -n "$SPIT_IMG" && -f "$SPIT_IMG" ]] && cp "$SPIT_IMG" "$STAGE/boot/spitfire.img"
cp -a "$ROOT/installer" "$STAGE/install/"
cp -a "$ROOT/userland" "$STAGE/system/userland"
cp -a "$ROOT/desktop" "$STAGE/system/desktop"
cp -a "$ROOT/services" "$STAGE/system/services"
cp -a "$ROOT/boot" "$STAGE/system/boot"
if [[ -n "${CHIMERA_AURORA_BACKGROUND:-}" && -f "$CHIMERA_AURORA_BACKGROUND" ]]; then mkdir -p "$STAGE/install/assets/aurora"; cp "$CHIMERA_AURORA_BACKGROUND" "$STAGE/install/assets/aurora/Aurora-Wayland-Glass-Desktop.png"; fi
FINAL="$ISO_DIR/chimera-ii-os.iso"
if [[ -n "$BASE" && -f "$BASE" ]] && command -v xorriso >/dev/null 2>&1; then xorriso -indev "$BASE" -outdev "$FINAL" -map "$STAGE" /chimera -commit -end; else CHIMERA_KERNEL="$KERNEL" CHIMERA_OUTPUT_ISO="$FINAL" "$ROOT/iso/chimera-live-iso.sh"; fi
cp "$FINAL" "$ROOT/chimera-ii-os.iso"
sha256sum "$FINAL" | tee "$FINAL.sha256"
echo "Built $FINAL"
