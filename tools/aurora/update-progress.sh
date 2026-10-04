#!/usr/bin/env bash
set -Eeuo pipefail
STATE="${CHIMERA_AURORA_PROGRESS_STATE:-build/aurora-media/progress/state.json}"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ "$STATE" = /* ]] || STATE="$ROOT/$STATE"
mkdir -p "$(dirname -- "$STATE")"
PERCENT="${1:-0}"; STAGE="${2:-boot}"; EN="${3:-Loading Chimera II OS}"; AR="${4:-جارٍ تحميل Chimera II OS}"
RESULT="${5:-ok}"
ERROR_TEXT="${CHIMERA_BOOT_ERROR:-}"
case "$PERCENT" in ''|*[!0-9]*) echo "invalid progress: $PERCENT" >&2; exit 2;; esac
(( PERCENT > 100 )) && PERCENT=100
json_escape(){ python3 -c 'import json,sys; print(json.dumps(sys.argv[1],ensure_ascii=False))' "$1"; }
EN_JSON="$(json_escape "$EN")"; AR_JSON="$(json_escape "$AR")"; STAGE_JSON="$(json_escape "$STAGE")"
TMP="${STATE}.tmp.$$"
printf '{"schema":"CHIMERA-AURORA-PROGRESS-2","percent":%s,"stage":%s,"message_en":%s,"message_ar":%s,"style":"glass-neon"}\n' "$PERCENT" "$STAGE_JSON" "$EN_JSON" "$AR_JSON" > "$TMP"
mv -f "$TMP" "$STATE"

# Runtime learning telemetry. Stage duration is measured from the previous
# transition, and CPU/memory/IO are normalized to stable percentages.
LEARN_ROOT="${CHIMERA_BOOT_LEARNING_ROOT:-$ROOT/build/boot-learning}"
mkdir -p "$LEARN_ROOT"
NOW_MS="$(date +%s%3N 2>/dev/null || echo 0)"
LAST_STAGE_FILE="$LEARN_ROOT/last-stage"
LAST_TS_FILE="$LEARN_ROOT/last-stage-ms"
LAST_STAGE="$(cat "$LAST_STAGE_FILE" 2>/dev/null || true)"
LAST_TS="$(cat "$LAST_TS_FILE" 2>/dev/null || echo "$NOW_MS")"
DURATION=0
if [[ "$LAST_STAGE" != "$STAGE" && "$LAST_TS" =~ ^[0-9]+$ && "$NOW_MS" =~ ^[0-9]+$ ]]; then
  DURATION=$(( NOW_MS - LAST_TS ))
  (( DURATION < 0 )) && DURATION=0
fi
printf '%s\n' "$STAGE" > "$LAST_STAGE_FILE"
printf '%s\n' "$NOW_MS" > "$LAST_TS_FILE"

CPU="$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo 0)"
MEM_PCT="$(awk '/MemTotal:/{t=$2}/MemAvailable:/{a=$2} END{if(t>0) printf "%.2f",(a/t)*100; else print 0}' /proc/meminfo 2>/dev/null || echo 0)"
IO="$(sed -n 's/.*avg10=\([0-9.]*\).*/\1/p' /proc/pressure/io 2>/dev/null | head -1 || echo 0)"
CPU="${CPU:-0}"; MEM_PCT="${MEM_PCT:-0}"; IO="${IO:-0}"
printf '%s,%s,%s,%s,%s,%s,%s\n' "$STAGE" "$PERCENT" "$DURATION" "$CPU" "$MEM_PCT" "$IO" "$RESULT" >> "$LEARN_ROOT/events.jsonl"

if [[ -n "$ERROR_TEXT" ]]; then
  printf '%s | stage=%s | percent=%s | result=%s\n' "$ERROR_TEXT" "$STAGE" "$PERCENT" "$RESULT" >> "$LEARN_ROOT/errors.log"
fi

# If the runtime recovery binary is installed, let it perform only its
# non-destructive, policy-constrained preparation pass.
if command -v chimera-runtime-recovery >/dev/null 2>&1; then
  CHIMERA_BOOT_LEARNING_ROOT="$LEARN_ROOT" \
  CHIMERA_BOOT_ERROR_LOG="$LEARN_ROOT/errors.log" \
  chimera-runtime-recovery once >/dev/null 2>&1 || true
fi
