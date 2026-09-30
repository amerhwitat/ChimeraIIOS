#!/bin/sh
set -eu
ROOT=${1:-/}
LOG=/var/log/mesgs
mkdir -p "$ROOT$LOG" "$ROOT/var/log/mesgs/archive"
printf '[INST] Runtime driver manager available\n' >> "$ROOT$LOG/mesgs" 2>/dev/null || true
if [ -x "$ROOT/usr/bin/chimera-driver-manager.sh" ]; then
  "$ROOT/usr/bin/chimera-driver-manager.sh" inventory || true
  "$ROOT/usr/bin/chimera-driver-manager.sh" search || true
fi
if [ -x "$ROOT/usr/bin/chimera-logrotate.sh" ]; then "$ROOT/usr/bin/chimera-logrotate.sh" || true; fi
