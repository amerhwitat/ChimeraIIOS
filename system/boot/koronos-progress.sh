#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: system/boot/koronos-progress.sh

Usage:
  system/boot/koronos-progress.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
