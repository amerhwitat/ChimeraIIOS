#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Generate and stage every Aurora artwork/icon asset into a Koronos ISO tree.

Usage:
  tools/aurora/stage-generated-iso-artwork.sh ISO_ROOT

The output includes boot/live/installer/recovery artwork, progress media, all
compiled-in Aurora SVG icons, all generated application SVG icons, and hicolor
icon-theme files. It validates the generated icon counts and source files.
HELP
  exit 0
fi

ISO_ROOT="${1:?usage: stage-generated-iso-artwork.sh ISO_ROOT}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
MEDIA="$ROOT/build/aurora-media"
NATIVE_ICONS="$ROOT/build/aurora-icons"
APP_ICONS="$ROOT/build/aurora-app-icons"

bash "$ROOT/tools/aurora/build-visual-assets.sh" "$MEDIA"
python3 "$ROOT/tools/aurora/export-icon-theme.py" --output "$NATIVE_ICONS"
python3 "$ROOT/tools/aurora/export-app-icon-theme.py" \
  --sprite "$ROOT/desktop/app-icons/catalog.svg" \
  --manifest "$ROOT/desktop/app-icons/manifest.json" \
  --output "$APP_ICONS"

python3 - "$NATIVE_ICONS/manifest.json" "$APP_ICONS/manifest.json" "$MEDIA/manifest.json" <<'PY'
import json,pathlib,sys
native=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
apps=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
media=json.loads(pathlib.Path(sys.argv[3]).read_text(encoding="utf-8"))
if native.get("count",0)<1: raise SystemExit("Aurora compiled-in icon export is empty")
if apps.get("count")!=133: raise SystemExit(f"expected 133 Aurora app icons, got {apps.get('count')}")
for row in native.get("icons",[]):
    if not (pathlib.Path(sys.argv[1]).parent/row["file"]).is_file(): raise SystemExit(f"missing native icon {row}")
for row in apps.get("icons",[]):
    if not (pathlib.Path(sys.argv[2]).parent/row["file"]).is_file(): raise SystemExit(f"missing app icon {row}")
for rel in ("backgrounds/boot.png","backgrounds/desktop.png","menus/default.png",
            "splash/aurora-splash.png","installer/aurora-installer.png",
            "recovery/aurora-recovery.png","diagnostics/aurora-diagnostics.png",
            "live/aurora-live.png","mobile/aurora-mobile.png","Init.mp4",
            "progress/state.json","progress/stages.json","progress/style.json"):
    if not (pathlib.Path(sys.argv[3]).parent/rel).is_file(): raise SystemExit(f"missing generated Aurora media {rel}")
print(f"Validated {native['count']} native Aurora icons, {apps['count']} app icons and all boot/desktop artwork.")
PY

mkdir -p "$ISO_ROOT/boot/visual/aurora-media" \
  "$ISO_ROOT/desktop/aurora/assets" "$ISO_ROOT/desktop/aurora/icons/generated" \
  "$ISO_ROOT/desktop/app-icons/icons" \
  "$ISO_ROOT/usr/share/icons/chimera-aurora/scalable/apps" \
  "$ISO_ROOT/usr/share/icons/hicolor/scalable/apps" \
  "$ISO_ROOT/usr/share/chimera/aurora/icons" \
  "$ISO_ROOT/usr/share/chimera/aurora/app-icons"

cp -a "$MEDIA/." "$ISO_ROOT/boot/visual/aurora-media/"
cp -a "$MEDIA/." "$ISO_ROOT/desktop/aurora/assets/"
cp -a "$MEDIA/." "$ISO_ROOT/usr/share/chimera/aurora/"
cp -a "$NATIVE_ICONS/." "$ISO_ROOT/desktop/aurora/icons/generated/"
cp -a "$NATIVE_ICONS/." "$ISO_ROOT/usr/share/icons/chimera-aurora/"
cp -a "$NATIVE_ICONS/." "$ISO_ROOT/usr/share/chimera/aurora/icons/"
cp -a "$APP_ICONS/." "$ISO_ROOT/desktop/app-icons/icons/"
cp -a "$APP_ICONS/." "$ISO_ROOT/usr/share/chimera/aurora/app-icons/"
cp -a "$NATIVE_ICONS"/chimera-*.svg "$ISO_ROOT/usr/share/icons/chimera-aurora/scalable/apps/"
cp -a "$APP_ICONS"/chimera-*.svg "$ISO_ROOT/usr/share/icons/hicolor/scalable/apps/"
cp -f "$ROOT/desktop/app-icons/catalog.svg" "$ROOT/desktop/app-icons/manifest.json" "$ISO_ROOT/desktop/app-icons/"

for stage in spitfire jasper grub koronos; do
  mkdir -p "$ISO_ROOT/boot/$stage"
  cp -f "$MEDIA/Init.mp4" "$ISO_ROOT/boot/$stage/Init.mp4"
  cp -f "$MEDIA/backgrounds/boot.png" "$ISO_ROOT/boot/$stage/aurora-boot.png"
  [[ -s "$ROOT/boot/boot-artwork-manifest.json" ]] && cp -f "$ROOT/boot/boot-artwork-manifest.json" "$ISO_ROOT/boot/$stage/"
done
for pair in \
  "spitfire:spitfire_background.svg" \
  "jasper:jasper_background.svg" \
  "grub:aurora_boot_splash.svg" \
  "koronos:aurora_boot_splash.svg"; do
  stage="${pair%%:*}"; file="${pair#*:}"
  [[ -s "$ROOT/boot/splash/$file" ]] && cp -f "$ROOT/boot/splash/$file" "$ISO_ROOT/boot/$stage/"
done

test "$(find "$ISO_ROOT/usr/share/icons/hicolor/scalable/apps" -maxdepth 1 -type f -name 'chimera-*.svg' | wc -l)" -eq 133
test "$(find "$ISO_ROOT/usr/share/icons/chimera-aurora/scalable/apps" -maxdepth 1 -type f -name 'chimera-*.svg' | wc -l)" -ge 1
test -s "$ISO_ROOT/desktop/aurora/assets/manifest.json"
test -s "$ISO_ROOT/usr/share/chimera/aurora/progress/stages.json"
echo "Staged complete Aurora artwork, generated icons, and boot/desktop progress media into $ISO_ROOT"
