#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
OUT="${1:-$ROOT/build/aurora-media}"
LIB="${CHIMERA_AURORA_LIBRARY_DIR:-$ROOT/desktop/aurora/assets/library}"
DEFAULTS="${CHIMERA_AURORA_DEFAULT_ARTWORK_DIR:-$ROOT/build/aurora-default-artwork}"
mkdir -p "$OUT"/{backgrounds,splash,progress,menus,recovery,installer,diagnostics,live,mobile}

copy_first() {
  local dest="$1"; shift
  local src
  for src in "$@"; do
    if [[ -s "$src" ]]; then cp -f "$src" "$OUT/$dest"; return 0; fi
  done
  return 1
}
convert_svg() {
  local src="$1" dest="$2"
  command -v rsvg-convert >/dev/null 2>&1 || return 1
  rsvg-convert -w 1920 -h 1080 "$src" -o "$dest"
}
"$ROOT/tools/aurora/generate-default-artwork.sh" "$DEFAULTS"

# Prefer supplied/Library artwork; otherwise use deterministic generated artwork.
copy_first backgrounds/boot.jpg   "$LIB/Aurora Wayland Desktop - boot background.jpg"   "$ROOT/boot/jasper/background.jpg" || convert_svg "$DEFAULTS/aurora-boot.svg" "$OUT/backgrounds/boot.png"
copy_first backgrounds/desktop.png   "$LIB/Aurora Wayland Glass Desktop.png"   "$LIB/Aurora-Wayland-Glass-Desktop.png(1).jpg" || convert_svg "$DEFAULTS/aurora-desktop.svg" "$OUT/backgrounds/desktop.png"
copy_first backgrounds/showcase.png   "$LIB/Aurora Wayland Desktop Showcase.png" || convert_svg "$DEFAULTS/aurora-splash.svg" "$OUT/backgrounds/showcase.png"
copy_first menus/default.png   "$LIB/Aurora-Wayland-Glass-Desktop.png(1).jpg"   "$LIB/Aurora Wayland Glass Desktop.png" || convert_svg "$DEFAULTS/aurora-menu.svg" "$OUT/menus/default.png"

# Normalize supplied raster artwork to real PNG data.
normalize_png() {
  local dest="$1" src="$2" tmp
  [[ -s "$src" ]] || return 0
  tmp="$(mktemp --suffix=.png "${dest}.XXXXXX")"
  if convert "$src" -resize 1920x1080^ -gravity center -extent 1920x1080 PNG32:"$tmp" 2>/dev/null && [[ -s "$tmp" ]]; then
    mv -f "$tmp" "$dest"
  else
    rm -f "$tmp"
    return 1
  fi
}
if [[ -s "$OUT/backgrounds/boot.jpg" ]]; then
  normalize_png "$OUT/backgrounds/boot.png" "$OUT/backgrounds/boot.jpg"
  rm -f "$OUT/backgrounds/boot.jpg"
fi
normalize_png "$OUT/backgrounds/desktop.png" "$OUT/backgrounds/desktop.png"
normalize_png "$OUT/backgrounds/showcase.png" "$OUT/backgrounds/showcase.png"
normalize_png "$OUT/menus/default.png" "$OUT/menus/default.png"

for spec in   "splash/aurora-splash.png aurora-splash.svg"   "installer/aurora-installer.png aurora-installer.svg"   "recovery/aurora-recovery.png aurora-recovery.svg"   "diagnostics/aurora-diagnostics.png aurora-diagnostics.svg"   "live/aurora-live.png aurora-live.svg"   "mobile/aurora-mobile.png aurora-mobile.svg"; do
  set -- $spec
  convert_svg "$DEFAULTS/$2" "$OUT/$1"
done

"$ROOT/tools/generate-aurora-media.sh" "$OUT"

cat > "$OUT/progress/stages.json" <<'EOF'
{"schema":"CHIMERA-AURORA-PROGRESS-2","visual_contract":"aurora-progress-v2","stages":[
{"id":"firmware","percent":5,"en":"Firmware","ar":"البرامج الثابتة"},
{"id":"hardware","percent":15,"en":"Hardware detection","ar":"اكتشاف العتاد"},
{"id":"memory","percent":25,"en":"Memory and SMP","ar":"الذاكرة والمعالجة المتعددة"},
{"id":"drivers","percent":38,"en":"Drivers","ar":"برامج التشغيل"},
{"id":"filesystem","percent":52,"en":"Filesystem","ar":"نظام الملفات"},
{"id":"network","percent":66,"en":"Network","ar":"الشبكة"},
{"id":"services","percent":78,"en":"Kore services","ar":"خدمات Kore"},
{"id":"nbit","percent":88,"en":"N-bit runtime","ar":"وقت تشغيل N-bit"},
{"id":"aurora","percent":96,"en":"Aurora","ar":"Aurora"},
{"id":"ready","percent":100,"en":"Desktop ready","ar":"سطح المكتب جاهز"}]}
EOF
cat > "$OUT/progress/state.json" <<'EOF'
{"percent":0,"stage":"firmware","message_en":"Starting Chimera II OS","message_ar":"بدء تشغيل Chimera II OS"}
EOF
cat > "$OUT/progress/style.json" <<'EOF'
{"schema":"CHIMERA-AURORA-PROGRESS-2","style":"glass-neon","height_px":14,"radius_px":7,"track_alpha":0.24,"fill_alpha":0.94,"glow":true,"indeterminate":false,"show_percent":true,"show_stage":true,"bilingual":true,"animation_ms":420}
EOF
cat > "$OUT/manifest.json" <<EOF
{"schema":"CHIMERA-AURORA-MEDIA-3","init_video":"Init.mp4","progress_state":"progress/state.json","progress_stages":"progress/stages.json","progress_style":"progress/style.json","artwork_generated_fallback":true,"assets":{"boot":"backgrounds/boot.png","desktop":"backgrounds/desktop.png","showcase":"backgrounds/showcase.png","menus":"menus/default.png","splash":"splash/aurora-splash.png","installer":"installer/aurora-installer.png","recovery":"recovery/aurora-recovery.png","diagnostics":"diagnostics/aurora-diagnostics.png","live":"live/aurora-live.png","mobile":"mobile/aurora-mobile.png"}}
EOF
printf '[INFO] Aurora visual assets generated in %s\n' "$OUT"
