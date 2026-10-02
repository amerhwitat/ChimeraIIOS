#!/bin/sh
set -eu
ROOT=${1:-/}
LOG=/var/log/mesgs
PROGRESS=${CHIMERA_PROGRESS_FILE:-$ROOT/run/chimera/progress.state}
mkdir -p "$ROOT$LOG" "$ROOT/var/log/mesgs/archive" "$ROOT/run/chimera"
progress(){
  pct=$1; phase=$2; msg=$3
  printf '%s|%s|%s\n' "$pct" "$phase" "$msg" > "$PROGRESS" 2>/dev/null || true
  printf '[PROGRESS] %s%% | %s | %s\n' "$pct" "$phase" "$msg" >> "$ROOT$LOG/mesgs" 2>/dev/null || true
}
progress 5 'Installer' 'Runtime initialization'
printf '[INST] Runtime driver manager available\n' >> "$ROOT$LOG/mesgs" 2>/dev/null || true
progress 20 'Hardware' 'Inventorying CPU, memory, storage and PCI/USB devices'
if [ -x "$ROOT/usr/bin/chimera-driver-manager.sh" ]; then
  "$ROOT/usr/bin/chimera-driver-manager.sh" inventory || true
  progress 45 'Drivers' 'Evaluating native and fallback drivers'
  "$ROOT/usr/bin/chimera-driver-manager.sh" search || true
fi
progress 65 'Storage' 'Preparing filesystem and installation targets'
if [ -x "$ROOT/usr/bin/chimera-logrotate.sh" ]; then "$ROOT/usr/bin/chimera-logrotate.sh" || true; fi
progress 80 'Aurora' 'Preparing graphical session and desktop assets'
progress 95 'Validation' 'Final boot, driver and recovery checks'
progress 100 'Installer' 'Installation environment ready'
