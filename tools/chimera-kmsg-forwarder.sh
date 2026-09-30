#!/bin/sh
set -eu
LOG=/var/log/mesgs
mkdir -p /var/log/mesgs/archive
touch "$LOG"
if [ -r /dev/kmsg ]; then
  while IFS= read -r line; do
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line" >> "$LOG"
  done < /dev/kmsg
elif [ -r /proc/kmsg ]; then
  while IFS= read -r line; do
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line" >> "$LOG"
  done < /proc/kmsg
else
  printf '%s [KLOG] Kernel message device unavailable; console logging remains active.\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  sleep infinity
fi
