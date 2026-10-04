#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/boot/chimera-boot-visual.sh

Usage:
  tools/boot/chimera-boot-visual.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

ROOT="${CHIMERA_REPO_ROOT:-/usr/share/chimera}"
ASSET_DIR="${CHIMERA_BOOT_ASSET_DIR:-/boot/visual}"
RUN_DIR="${CHIMERA_RUNTIME_DIR:-/run/chimera}"
LOG="${CHIMERA_BOOT_LOG:-$RUN_DIR/boot.log}"
BG="${CHIMERA_AURORA_BACKGROUND_JPG:-$ASSET_DIR/aurora-wayland-glass.jpg}"
VIDEO="${CHIMERA_BOOT_VIDEO:-$ASSET_DIR/chimera-intro.mp4}"

mkdir -p "$RUN_DIR"
: > "$LOG"
log(){ printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG"; }
log "Chimera II visual boot runtime starting"
log "Aurora background: $BG"

if [[ -f "$BG" ]]; then
  if command -v swaybg >/dev/null 2>&1; then
    swaybg -i "$BG" -m fill >/tmp/chimera-aurora-background.log 2>&1 &
    echo $! > "$RUN_DIR/aurora-background.pid"
    log "[ OK ] Aurora background compositor"
  elif command -v feh >/dev/null 2>&1; then
    feh --bg-fill "$BG" >/tmp/chimera-aurora-background.log 2>&1 || true
    log "[ OK ] Aurora background image"
  else
    log "[ .. ] Aurora background staged (no background provider yet)"
  fi
else
  log "[WARN] Aurora background is missing"
fi

if [[ -f "$VIDEO" ]]; then
  if command -v gst-launch-1.0 >/dev/null 2>&1; then
    gst-launch-1.0 -q filesrc location="$VIDEO" ! decodebin ! videoconvert ! autovideosink sync=false >/tmp/chimera-boot-video.log 2>&1 &
    echo $! > "$RUN_DIR/boot-video.pid"
    log "[ OK ] Aurora MP4 boot video"
  elif command -v mpv >/dev/null 2>&1; then
    mpv --fs --no-terminal --loop-file=inf "$VIDEO" >/tmp/chimera-boot-video.log 2>&1 &
    echo $! > "$RUN_DIR/boot-video.pid"
    log "[ OK ] Aurora MP4 boot video (mpv)"
  else
    log "[WARN] MP4 staged but no GStreamer/mpv provider is installed"
  fi
else
  log "[WARN] Chimera boot video is missing"
fi

for svc in spitfire jasper koronos kore spotnik aegis nucleus; do
  if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$svc" 2>/dev/null; then
    log "[ OK ] service/$svc"
  else
    log "[ .. ] service/$svc (waiting)"
  fi
done
log "[ OK ] boot visual layer initialized"
log "[ OK ] boot log available at $LOG"

if [[ "${CHIMERA_BOOT_LOG_OVERLAY:-1}" == "1" ]]; then
  if command -v foot >/dev/null 2>&1; then
    foot --app-id=chimera-boot-log --title="Chimera II OS Boot Log" sh -c 'tail -F /run/chimera/boot.log' >/tmp/chimera-boot-overlay.log 2>&1 &
  elif command -v alacritty >/dev/null 2>&1; then
    alacritty --title "Chimera II OS Boot Log" -e sh -c 'tail -F /run/chimera/boot.log' >/tmp/chimera-boot-overlay.log 2>&1 &
  fi
fi
