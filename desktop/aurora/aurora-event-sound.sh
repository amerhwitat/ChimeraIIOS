#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$ROOT/assets/sounds/manifest.json"
SOUND_DIR="$ROOT/assets/sounds"
EVENT="${1:-}"
VOLUME="${2:-${CHIMERA_SOUND_VOLUME:-0.55}}"

known_event(){
  local event="${1:-}"
  python3 - "$MANIFEST" "$event" <<'PY'
import json,sys
path,event=sys.argv[1:]
try:
    data=json.load(open(path,encoding='utf-8'))
    print(data.get('events',{}).get(event,''))
except Exception:
    print('')
PY
}

if [[ "${1:-}" == --known ]]; then known_event "${2:-}"; exit 0; fi
[[ -n "$EVENT" ]] || exit 0
[[ "${CHIMERA_SOUND_ENABLED:-1}" != 0 ]] || exit 0
file="$(known_event "$EVENT")"
[[ -n "$file" && -f "$SOUND_DIR/$file" ]] || exit 0

player=()
if command -v pw-play >/dev/null 2>&1; then player=(pw-play "$SOUND_DIR/$file")
elif command -v paplay >/dev/null 2>&1; then player=(paplay "$SOUND_DIR/$file")
elif command -v aplay >/dev/null 2>&1; then player=(aplay -q "$SOUND_DIR/$file")
elif command -v ffplay >/dev/null 2>&1; then player=(ffplay -nodisp -autoexit -loglevel quiet "$SOUND_DIR/$file")
else exit 0; fi

"${player[@]}" >/dev/null 2>&1 &
exit 0
