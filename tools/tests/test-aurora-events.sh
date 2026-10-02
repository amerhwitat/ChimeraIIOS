#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVENT="$ROOT/desktop/aurora/aurora-event-sound.sh"
[[ -x "$EVENT" ]] || { echo "missing executable: $EVENT" >&2; exit 1; }
[[ "$($EVENT --known menu_select)" == "menu-select.wav" ]]
[[ "$($EVENT --known unknown-event)" == "" ]]
CHIMERA_SOUND_ENABLED=0 "$EVENT" menu_select >/dev/null 2>&1
printf 'PASS: Aurora event sound contract\n'
