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
mkdir -p "$LOG_DIR" "$ARCHIVE_DIR"
if [ -s "$LOG_FILE" ]; then
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  mv "$LOG_FILE" "$ARCHIVE_DIR/mesgs.$ts"
  : > "$LOG_FILE"
  if [ "$COMPRESS" = 1 ] && command -v gzip >/dev/null 2>&1; then gzip -f "$ARCHIVE_DIR/mesgs.$ts"; fi
fi
ls -1t "$ARCHIVE_DIR"/mesgs.* 2>/dev/null | awk "NR>$KEEP_ARCHIVES" | while IFS= read -r f; do rm -f "$f"; done
echo "Chimera log rotation complete: $LOG_FILE"
