#!/bin/sh
set -eu
CONFIG=${CHIMERA_LOG_CONFIG:-/etc/chimera/logging.conf}
LOG_DIR=/var/log/mesgs
LOG_FILE="$LOG_DIR/mesgs"
ARCHIVE_DIR="$LOG_DIR/archive"
MAX_BYTES=52428800
KEEP_ARCHIVES=30
COMPRESS=1
[ -f "$CONFIG" ] && . "$CONFIG" || true
parse_period(){
  v="$1"
  case "$v" in
    *s) echo "${v%s}";;
    *m) echo $((${v%m}*60));;
    *h) echo $((${v%h}*3600));;
    *d) echo $((${v%d}*86400));;
    *w) echo $((${v%w}*604800));;
    *) return 1;;
  esac
}
if [ "${1:-}" = "--period" ]; then
  seconds=$(parse_period "${2:-}") || { echo "usage: chimera-logrotate --period 1h|24h|7d"; exit 2; }
  mkdir -p "$(dirname "$CONFIG")"
  { echo "ROTATE_SECONDS=$seconds"; echo "MAX_BYTES=$MAX_BYTES"; echo "KEEP_ARCHIVES=$KEEP_ARCHIVES"; echo "COMPRESS=$COMPRESS"; } > "$CONFIG"
  echo "Chimera log rotation period set to $seconds seconds in $CONFIG"
  exit 0
fi
mkdir -p "$LOG_DIR" "$ARCHIVE_DIR"
if [ -s "$LOG_FILE" ]; then
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  mv "$LOG_FILE" "$ARCHIVE_DIR/mesgs.$ts"
  : > "$LOG_FILE"
  if [ "$COMPRESS" = 1 ] && command -v gzip >/dev/null 2>&1; then gzip -f "$ARCHIVE_DIR/mesgs.$ts"; fi
fi
ls -1t "$ARCHIVE_DIR"/mesgs.* 2>/dev/null | awk "NR>$KEEP_ARCHIVES" | while IFS= read -r f; do rm -f "$f"; done
echo "Chimera log rotation complete: $LOG_FILE"
