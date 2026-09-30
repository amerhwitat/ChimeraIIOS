#!/bin/sh
set -eu
OUT=${1:-/var/crash/chimera/manual-$(date -u +%Y%m%dT%H%M%SZ)}
mkdir -p "$OUT"
if [ -r /proc/kcore ] && [ "$(id -u 2>/dev/null || echo 1)" = 0 ]; then dd if=/proc/kcore of="$OUT/memory.kcore" bs=1M status=none 2>/dev/null || true; else cat /proc/meminfo > "$OUT/memory.map"; printf 'Physical RAM dumping requires a privileged native kernel crash-dump provider.\n' > "$OUT/memory.note"; fi
printf '%s\n' "$OUT"
