#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OUT="${1:-$ROOT/desktop/aurora/assets}"
BG="${CHIMERA_AURORA_SOURCE_IMAGE:-}"

mkdir -p "$OUT/sounds" "$OUT/progress"

if [[ -z "$BG" ]]; then
  for candidate in \
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

if [[ -n "$BG" && -f "$BG" ]] && command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -loglevel error -loop 1 -i "$BG" -t 12 \
    -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p,drawtext=fontcolor=white:fontsize=42:text='CHIMERA II OS':x=(w-text_w)/2:y=270,drawtext=fontcolor=white:fontsize=22:text='AURORA INITIALIZING':x=(w-text_w)/2:y=325,drawbox=x=340:y=390:w=600:h=12:color=white@0.22:t=fill,drawbox=x=340:y=390:w='600*t/12':h=12:color=white@0.9:t=fill" \
    -r 30 -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -movflags +faststart "$OUT/Init.mp4"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  while IFS=: read -r n f1 f2; do
    [[ -s "$OUT/sounds/$n.wav" ]] && continue
    ffmpeg -y -loglevel error \
      -f lavfi -i "sine=frequency=$f1:duration=0.18" \
      -f lavfi -i "sine=frequency=$f2:duration=0.18" \
      -filter_complex '[0:a][1:a]amix=inputs=2:duration=longest,afade=t=out:st=0.12:d=0.06,volume=0.18' \
      -c:a pcm_s16le "$OUT/sounds/$n.wav"
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

[[ -s "$OUT/Init.mp4" ]] || printf '%s\n' '[WARN] Init.mp4 could not be generated; static fallback remains valid.' >&2
