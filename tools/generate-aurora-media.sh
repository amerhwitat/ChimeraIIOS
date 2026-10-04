#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/generate-aurora-media.sh

Usage:
  tools/generate-aurora-media.sh [options] [arguments]

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
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OUT="${1:-$ROOT/desktop/aurora/assets}"
BG="${CHIMERA_AURORA_SOURCE_IMAGE:-}"
INIT_VIDEO="${CHIMERA_AURORA_INIT_VIDEO:-}"

mkdir -p "$OUT/sounds" "$OUT/progress"

if [[ -z "$INIT_VIDEO" ]]; then
  for candidate in \
    "$OUT/Init.mp4" \
    "$ROOT/desktop/aurora/assets/library/Init.mp4" \
    "$ROOT/desktop/aurora/assets/Init.mp4" \
    "$ROOT/build/aurora-media/Init.mp4" \
    "$ROOT/build/iso/usr/share/chimera/aurora/Init.mp4" \
    "$ROOT/boot/jasper/Init.mp4" \
    "$ROOT/Init.mp4"; do
    if [[ -s "$candidate" ]]; then
      INIT_VIDEO="$candidate"
      break
    fi
  done
fi

if [[ -n "$INIT_VIDEO" ]]; then
  if [[ ! -f "$INIT_VIDEO" ]]; then
    printf '%s\n' "[ERROR] CHIMERA_AURORA_INIT_VIDEO does not exist: $INIT_VIDEO" >&2
    exit 1
  fi
  if [[ ! -s "$INIT_VIDEO" ]]; then
    printf '%s\n' "[ERROR] CHIMERA_AURORA_INIT_VIDEO is empty: $INIT_VIDEO" >&2
    exit 1
  fi
  if command -v ffprobe >/dev/null 2>&1 && ! ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 "$INIT_VIDEO" >/dev/null; then
    printf '%s\n' "[ERROR] Supplied Init.mp4 is not a readable video: $INIT_VIDEO" >&2
    exit 1
  fi
  if [[ "$(realpath -m "$INIT_VIDEO")" != "$(realpath -m "$OUT/Init.mp4")" ]]; then
    cp -f "$INIT_VIDEO" "$OUT/Init.mp4"
  fi
  echo "[INFO] Using Aurora Init.mp4: $INIT_VIDEO"
fi

if [[ -z "$BG" ]]; then
  for candidate in \
    "$OUT/backgrounds/boot.jpg" \
    "$OUT/backgrounds/boot.png" \
    "$ROOT/boot/jasper/background.jpg" \
    "$ROOT/boot/jasper/background.png" \
    "$ROOT/desktop/aurora/assets/Aurora-Wayland-Glass-Desktop.png(1).jpg" \
    "$ROOT/desktop/aurora/assets/library/Aurora Wayland Desktop - boot background.jpg"; do
    if [[ -f "$candidate" ]]; then
      BG="$candidate"
      break
    fi
  done
fi

if [[ ! -s "$OUT/Init.mp4" && -n "$BG" && -f "$BG" ]] && command -v ffmpeg >/dev/null 2>&1; then
  echo "[INFO] Generating Aurora Init.mp4 from: $BG"
  ffmpeg -y -loglevel error -loop 1 -i "$BG" -t 12 \
    -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p,drawtext=fontcolor=white:fontsize=42:text='CHIMERA II OS':x=(w-text_w)/2:y=270,drawtext=fontcolor=white:fontsize=22:text='AURORA INITIALIZING':x=(w-text_w)/2:y=325,drawbox=x=340:y=390:w=600:h=12:color=white@0.22:t=fill,drawbox=x=340:y=390:w='600*t/12':h=12:color=white@0.9:t=fill" \
    -r 30 -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -movflags +faststart "$OUT/Init.mp4"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  while IFS=: read -r n f1 f2; do
    [[ -s "$OUT/sounds/$n.wav" ]] && continue
    ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=$f1:duration=0.18" -f lavfi -i "sine=frequency=$f2:duration=0.18" -filter_complex '[0:a][1:a]amix=inputs=2:duration=longest,afade=t=out:st=0.12:d=0.06,volume=0.18' -c:a pcm_s16le "$OUT/sounds/$n.wav"
  done <<'EOF'
startup:440:660
menu-open:520:780
menu-focus:660:990
menu-select:784:1176
menu-back:520:390
cancel:330:220
warning:440:330
error:220:165
success:523:784
device-connect:392:588
device-disconnect:294:196
install-step:587:880
recovery:349:523
shutdown:440:220
EOF
fi

cat > "$OUT/progress/state.json" <<'EOF'
{"percent":0,"stage":"firmware","message_en":"Starting Chimera II OS","message_ar":"بدء تشغيل Chimera II OS"}
EOF

if [[ ! -s "$OUT/Init.mp4" ]]; then
  printf '%s\n' '[ERROR] Aurora Init.mp4 is unavailable.' >&2
  printf '%s\n' '[ERROR] Import the Library Init.mp4 into desktop/aurora/assets/library/ or set CHIMERA_AURORA_INIT_VIDEO=/path/to/Init.mp4.' >&2
  exit 1
fi

echo "[INFO] Aurora Init.mp4 ready: $OUT/Init.mp4"
