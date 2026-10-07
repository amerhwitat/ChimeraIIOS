#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/aurora/build-visual-assets.sh

Usage:
  tools/aurora/build-visual-assets.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
  [[ -s "$src" ]] || return 1

  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -w 1920 -h 1080 "$src" -o "$dest"
    return $?
  fi

  # ImageMagick is the second supported offline converter. Do not let a
  # missing optional converter abort the entire branding stage.
  if command -v convert >/dev/null 2>&1; then
    convert -background none "$src" -resize 1920x1080 "$dest" 2>/dev/null
    return $?
  fi

  printf '[WARN] No SVG rasterizer available; retaining SVG fallback: %s\\n' "$src" >&2
  return 1
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

  # ImageMagick is optional. A missing converter must never abort the
  # branding stage when deterministic fallback PNGs can be generated below.
  if ! command -v convert >/dev/null 2>&1; then
    printf '[WARN] ImageMagick unavailable; keeping existing raster asset: %s\\n' "$src" >&2
    return 0
  fi

  tmp="$(mktemp --suffix=.png "${dest}.XXXXXX")"
  if convert "$src" -resize 1920x1080^ -gravity center -extent 1920x1080 PNG32:"$tmp" 2>/dev/null && [[ -s "$tmp" ]]; then
    mv -f "$tmp" "$dest"
  else
    rm -f "$tmp"
    printf '[WARN] Could not normalize Aurora raster asset: %s\\n' "$src" >&2
    return 0
  fi
}
if [[ -s "$OUT/backgrounds/boot.jpg" ]]; then
  normalize_png "$OUT/backgrounds/boot.png" "$OUT/backgrounds/boot.jpg"
  rm -f "$OUT/backgrounds/boot.jpg"
fi
normalize_png "$OUT/backgrounds/desktop.png" "$OUT/backgrounds/desktop.png"
normalize_png "$OUT/backgrounds/showcase.png" "$OUT/backgrounds/showcase.png"
normalize_png "$OUT/menus/default.png" "$OUT/menus/default.png"

# If no SVG rasterizer is installed, create valid deterministic PNGs directly
# with Python's standard library. This keeps the ISO branding contract intact
# without requiring ImageMagick or librsvg on the host.
generate_png_fallback() {
  local dest="$1" label="$2" subtitle="$3"
  [[ -s "$dest" ]] && return 0
  command -v python3 >/dev/null 2>&1 || {
    printf '[ERROR] No rasterizer available and python3 is missing; cannot create Aurora PNG: %s\\n' "$dest" >&2
    return 1
  }
  python3 - "$dest" "$label" "$subtitle" <<'PY'
import struct, sys, zlib
out, label, subtitle = sys.argv[1:4]
w, h = 1920, 1080
# Deterministic dark Aurora gradient with a subtle cyan/teal glow.
rows = []
for y in range(h):
    row = bytearray([0])
    fy = y / (h - 1)
    for x in range(w):
        fx = x / (w - 1)
        glow = max(0.0, 1.0 - (((fx - .20) / .55) ** 2 + ((fy - .22) / .55) ** 2))
        r = int(3 + 8 * (1 - fy) + 3 * glow)
        g = int(8 + 25 * (1 - fy) + 55 * glow)
        b = int(18 + 38 * (1 - fy) + 62 * glow)
        row.extend((r, g, b, 255))
    rows.append(row)
raw = b''.join(rows)
def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
png += chunk(b"tEXt", b"Title\0" + label.encode("utf-8"))
png += chunk(b"tEXt", b"Subtitle\0" + subtitle.encode("utf-8"))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")
with open(out, "wb") as fh:
    fh.write(png)
PY
}
generate_png_fallback "$OUT/backgrounds/boot.png" "CHIMERA II OS" "AURORA BOOT"
generate_png_fallback "$OUT/backgrounds/desktop.png" "CHIMERA II OS" "AURORA DESKTOP"
generate_png_fallback "$OUT/backgrounds/showcase.png" "CHIMERA II OS" "AURORA SHOWCASE"
generate_png_fallback "$OUT/menus/default.png" "CHIMERA II OS" "AURORA BOOT MENU"

for spec in \
  "splash/aurora-splash.png aurora-splash.svg" \
  "installer/aurora-installer.png aurora-installer.svg" \
  "recovery/aurora-recovery.png aurora-recovery.svg" \
  "diagnostics/aurora-diagnostics.png aurora-diagnostics.svg" \
  "live/aurora-live.png aurora-live.svg" \
  "mobile/aurora-mobile.png aurora-mobile.svg"; do
  set -- $spec
  convert_svg "$DEFAULTS/$2" "$OUT/$1" || {
    printf '[WARN] SVG rasterization unavailable for %s; generating deterministic PNG fallback.\\n' "$2" >&2
    generate_png_fallback "$OUT/$1" "CHIMERA II OS" "$(basename "$2" .svg | tr '-' ' ' | tr '[:lower:]' '[:upper:]')"
  }
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
