#!/bin/sh
set -eu
PAYLOAD=${1:?compressed payload}; shift
CACHE=/run/chimera/xexec
mkdir -p "$CACHE"
base=$(basename "$PAYLOAD"); out="$CACHE/${base%.*}"
if [ -x "$out" ] && [ "$PAYLOAD" -ot "$out" ]; then exec "$out" "$@"; fi
case "$PAYLOAD" in
  *.zst) command -v zstd >/dev/null 2>&1 || exit 127; zstd -dc "$PAYLOAD" > "$out";;
  *.xz) command -v xz >/dev/null 2>&1 || exit 127; xz -dc "$PAYLOAD" > "$out";;
  *.gz) command -v gzip >/dev/null 2>&1 || exit 127; gzip -dc "$PAYLOAD" > "$out";;
  *) exit 2;;
esac
chmod 700 "$out"
exec "$out" "$@"
