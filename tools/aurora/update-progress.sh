#!/usr/bin/env bash
set -Eeuo pipefail
STATE="${CHIMERA_AURORA_PROGRESS_STATE:-build/aurora-media/progress/state.json}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$STATE" = /* ]] || STATE="$ROOT/$STATE"
mkdir -p "$(dirname -- "$STATE")"
PERCENT="${1:-0}"; STAGE="${2:-boot}"; EN="${3:-Loading Chimera II OS}"; AR="${4:-جارٍ تحميل Chimera II OS}"
case "$PERCENT" in ''|*[!0-9]*) echo "invalid progress: $PERCENT" >&2; exit 2;; esac
(( PERCENT > 100 )) && PERCENT=100
json_escape(){ python3 -c 'import json,sys; print(json.dumps(sys.argv[1],ensure_ascii=False))' "$1"; }
EN_JSON="$(json_escape "$EN")"; AR_JSON="$(json_escape "$AR")"; STAGE_JSON="$(json_escape "$STAGE")"
TMP="${STATE}.tmp.$$"
printf '{"schema":"CHIMERA-AURORA-PROGRESS-2","percent":%s,"stage":%s,"message_en":%s,"message_ar":%s,"style":"glass-neon"}\n' "$PERCENT" "$STAGE_JSON" "$EN_JSON" "$AR_JSON" > "$TMP"
mv -f "$TMP" "$STATE"
