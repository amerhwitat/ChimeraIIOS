#!/usr/bin/env bash
set -Eeuo pipefail
STATE="${CHIMERA_AURORA_PROGRESS_STATE:-build/aurora-media/progress/state.json}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$STATE" = /* ]] || STATE="$ROOT/$STATE"
mkdir -p "$(dirname -- "$STATE")"
PERCENT="${1:-0}"; STAGE="${2:-boot}"; EN="${3:-Loading Chimera II OS}"; AR="${4:-جارٍ تحميل Chimera II OS}"
RESULT="${5:-ok}"
case "$PERCENT" in ''|*[!0-9]*) echo "invalid progress: $PERCENT" >&2; exit 2;; esac
(( PERCENT > 100 )) && PERCENT=100
json_escape(){ python3 -c 'import json,sys; print(json.dumps(sys.argv[1],ensure_ascii=False))' "$1"; }
EN_JSON="$(json_escape "$EN")"; AR_JSON="$(json_escape "$AR")"; STAGE_JSON="$(json_escape "$STAGE")"
TMP="${STATE}.tmp.$$"
printf '{"schema":"CHIMERA-AURORA-PROGRESS-2","percent":%s,"stage":%s,"message_en":%s,"message_ar":%s,"style":"glass-neon"}\n' "$PERCENT" "$STAGE_JSON" "$EN_JSON" "$AR_JSON" > "$TMP"
mv -f "$TMP" "$STATE"
# Feed runtime boot telemetry into the recurrent learner.
LEARN_ROOT="${CHIMERA_BOOT_LEARNING_ROOT:-$ROOT/build/boot-learning}"
mkdir -p "$LEARN_ROOT"
CPU="$(awk '/^cpu /{print $2}' /proc/stat 2>/dev/null | head -1 || echo 0)"
MEM="$(awk '/MemAvailable:/{print $2}' /proc/meminfo 2>/dev/null || echo 0)"
IO="$(awk '/avg10=/{print $2}' /proc/pressure/io 2>/dev/null | head -1 || echo 0)"
printf '%s,%s,%s,%s,%s,%s,%s\n' "$STAGE" "$PERCENT" "0" "${CPU:-0}" "${MEM:-0}" "${IO:-0}" "$RESULT" >> "$LEARN_ROOT/events.jsonl"
