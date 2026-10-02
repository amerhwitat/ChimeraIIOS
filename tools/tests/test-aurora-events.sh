#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVENT="$ROOT/desktop/aurora/aurora-event-sound.sh"
[[ -f "$EVENT" ]] || { echo "missing: $EVENT" >&2; exit 1; }
[[ "$(bash "$EVENT" --known menu_select)" == "menu-select.wav" ]]
[[ "$(bash "$EVENT" --known unknown-event)" == "" ]]
CHIMERA_SOUND_ENABLED=0 bash "$EVENT" menu_select >/dev/null 2>&1
printf 'PASS: Aurora event sound contract\n'
