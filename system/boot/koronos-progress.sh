#!/usr/bin/env bash
set -Eeuo pipefail
STATE_DIR="${CHIMERA_PROGRESS_DIR:-/run/chimera}"
STATE_FILE="$STATE_DIR/koronos-progress.state"

write_state(){
  local percent="$1" phase="$2" message="$3" seq tmp
  [[ "$percent" =~ ^[0-9]+$ && "$percent" -ge 0 && "$percent" -le 100 ]] || { echo 'invalid percent' >&2; return 2; }
  [[ -n "$phase" && -n "$message" ]] || { echo 'phase/message required' >&2; return 2; }
  mkdir -p "$STATE_DIR"
  seq="$(date +%s%N 2>/dev/null || date +%s)"
  tmp="$STATE_FILE.tmp.$$"
  printf 'version=1\nsequence=%s\npercent=%s\nphase=%s\nmessage=%s\ntimestamp=%s\n' "$seq" "$percent" "$phase" "$message" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$tmp"
  mv -f "$tmp" "$STATE_FILE"
}

case "${1:-}" in
  set) [[ $# -ge 4 ]] || { echo 'usage: koronos-progress.sh set PERCENT PHASE MESSAGE' >&2; exit 2; }; write_state "$2" "$3" "$4";;
  get) [[ -f "$STATE_FILE" ]] && cat "$STATE_FILE" || { printf 'version=1\npercent=-1\nphase=unknown\nmessage=waiting\n'; exit 0; };;
  path) printf '%s\n' "$STATE_FILE";;
  *) echo 'usage: koronos-progress.sh {set|get|path}' >&2; exit 2;;
esac
