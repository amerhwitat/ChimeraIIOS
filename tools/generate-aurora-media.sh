#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/desktop/aurora/assets}"
BG="${CHIMERA_AURORA_SOURCE_IMAGE:-}"
mkdir -p "$OUT/sounds"
if [[ -z "$BG" ]]; then
  for candidate in "$ROOT/boot/jasper/background.jpg" "$ROOT/boot/jasper/background.png" "$ROOT/desktop/aurora/assets/Aurora-Wayland-Glass-Desktop.png(1).jpg"; do
    if [[ -f "$candidate" ]]; then BG="$candidate"; break; fi
  done
afi

if [[ -n "$BG" && -f "$BG" ]] && command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -loglevel error -loop 1 -i "$BG" -t 1.5 \
    -vf "scale=320:180:force_original_aspect_ratio=increase,crop=320:180,format=yuv420p,drawtext=fontcolor=white:fontsize=18:text='CHIMERA II OS':x=(w-text_w)/2:y=72,drawtext=fontcolor=white:fontsize=10:text='AURORA INITIALIZING':x=(w-text_w)/2:y=100" \
    -r 15 -c:v libx264 -preset ultrafast -crf 45 -movflags +faststart "$OUT/init.mp4"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  while IFS=: read -r n f1 f2; do
    [[ -f "$OUT/sounds/$n.wav" ]] && continue
    ffmpeg -y -loglevel error -f lavfi -i "sine=frequency=$f1:duration=0.18" -f lavfi -i "sine=frequency=$f2:duration=0.18" \
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

[[ -s "$OUT/init.mp4" ]] || printf '[WARN] init.mp4 could not be generated; static fallback remains valid.\n' >&2
