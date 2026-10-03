#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
OUT="${1:-$ROOT/build/aurora-media}"
LIB="${CHIMERA_AURORA_LIBRARY_DIR:-$ROOT/desktop/aurora/assets/library}"
mkdir -p "$OUT"/{backgrounds,splash,progress,menus}
copy_first(){ local dest="$1"; shift; local src; for src in "$@"; do if [[ -f "$src" ]]; then cp -f "$src" "$OUT/$dest"; return 0; fi; done; return 1; }
copy_first backgrounds/boot.jpg "$LIB/Aurora Wayland Desktop - boot background.jpg" "$ROOT/boot/jasper/background.jpg" || true
copy_first backgrounds/desktop.png "$LIB/Aurora Wayland Glass Desktop.png" "$LIB/Aurora-Wayland-Glass-Desktop.png(1).jpg" || true
copy_first backgrounds/showcase.png "$LIB/Aurora Wayland Desktop Showcase.png" || true
copy_first menus/default.png "$LIB/Aurora-Wayland-Glass-Desktop.png(1).jpg" "$LIB/Aurora Wayland Glass Desktop.png" || true
"$ROOT/tools/generate-aurora-media.sh" "$OUT"
cat > "$OUT/progress/stages.json" <<'EOF'
{"schema":"CHIMERA-AURORA-PROGRESS-1","stages":[{"id":"firmware","percent":5,"en":"Firmware","ar":"البرامج الثابتة"},{"id":"hardware","percent":15,"en":"Hardware detection","ar":"اكتشاف العتاد"},{"id":"memory","percent":25,"en":"Memory and SMP","ar":"الذاكرة والمعالجة المتعددة"},{"id":"drivers","percent":38,"en":"Drivers","ar":"برامج التشغيل"},{"id":"filesystem","percent":52,"en":"Filesystem","ar":"نظام الملفات"},{"id":"network","percent":66,"en":"Network","ar":"الشبكة"},{"id":"services","percent":78,"en":"Kore services","ar":"خدمات Kore"},{"id":"nbit","percent":88,"en":"N-bit runtime","ar":"وقت تشغيل N-bit"},{"id":"aurora","percent":96,"en":"Aurora","ar":"Aurora"},{"id":"ready","percent":100,"en":"Desktop ready","ar":"سطح المكتب جاهز"}]}
EOF
cat > "$OUT/progress/state.json" <<'EOF'
{"percent":0,"stage":"firmware","message_en":"Starting Chimera II OS","message_ar":"بدء تشغيل Chimera II OS"}
EOF
cat > "$OUT/manifest.json" <<EOF
{"schema":"CHIMERA-AURORA-MEDIA-2","init_video":"Init.mp4","progress_state":"progress/state.json","progress_stages":"progress/stages.json","assets":{"boot":"backgrounds/boot.jpg","desktop":"backgrounds/desktop.png","showcase":"backgrounds/showcase.png","menus":"menus/default.png"},"library_source":"${LIB}"}
EOF
printf '[INFO] Aurora visual assets generated in %s\n' "$OUT"
