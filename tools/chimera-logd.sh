#!/bin/sh
set -eu
CONFIG=\${CHIMERA_LOG_CONFIG:-/etc/chimera/logging.conf}
LOG_DIR=/var/log/mesgs
LOG_FILE="$LOG_DIR/mesgs"
ARCHIVE_DIR="$LOG_DIR/archive"
ROTATE_SECONDS=86400
MAX_BYTES=52428800
KEEP_ARCHIVES=30
COMPRESS=1
mkdir -p "$LOG_DIR" "$ARCHIVE_DIR"
[ -e /var/log/messages ] || ln -sf mesgs /var/log/messages 2>/dev/null || true
[ -f "$CONFIG" ] && . "$CONFIG" || true
touch "$LOG_FILE"
rotate_now() {
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  if [ -s "$LOG_FILE" ]; then
    mv "$LOG_FILE" "$ARCHIVE_DIR/mesgs.$ts"
    : > "$LOG_FILE"
    if [ "$COMPRESS" = 1 ] && command -v gzip >/dev/null 2>&1; then gzip -f "$ARCHIVE_DIR/mesgs.$ts"; fi
  fi
  ls -1t "$ARCHIVE_DIR"/mesgs.* 2>/dev/null | awk "NR>$KEEP_ARCHIVES" | while IFS= read -r f; do rm -f "$f"; done
}
last_rotate=$(date +%s)
while :; do
  now=$(date +%s)
  size=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
  if [ "$size" -ge "$MAX_BYTES" ] || [ $((now-last_rotate)) -ge "$ROTATE_SECONDS" ]; then
    rotate_now
    last_rotate=$now
  fi
  sleep 5
done
