#!/usr/bin/env bash
set -euo pipefail

ROOT=/usr/share/chimera
AURORA="$ROOT/aurora"
LOG_DIR="${XDG_RUNTIME_DIR:-/tmp}/chimera"
mkdir -p "$LOG_DIR"

log(){ printf '[Aurora] %s\n' "$*" >> "$LOG_DIR/aurora-desktop.log"; }

# Audio/video session daemons are user services on a normal Linux desktop.
# Start them explicitly for the live autologin path when systemd --user is not
# yet managing them.
if command -v pipewire >/dev/null 2>&1 && ! pgrep -u "$(id -u)" -x pipewire >/dev/null 2>&1; then
  pipewire >/dev/null 2>&1 &
fi
if command -v wireplumber >/dev/null 2>&1 && ! pgrep -u "$(id -u)" -x wireplumber >/dev/null 2>&1; then
  wireplumber >/dev/null 2>&1 &
fi

# Glass-style Aurora background. swaybg is intentionally a separate client so
# the compositor remains independent of wallpaper rendering.
if command -v swaybg >/dev/null 2>&1; then
  bg="${CHIMERA_AURORA_BACKGROUND:-$AURORA/ChimeraIIOS-Aurora-Wayland-Glass.jpg}"
  if [[ -r "$bg" ]]; then
    swaybg -m fill -i "$bg" >/tmp/aurora-swaybg.log 2>&1 &
    log "background started: $bg"
  fi
fi

# Modern top panel/taskbar. Waybar is optional; the compositor remains usable
# when it is unavailable on reduced hardware.
if command -v waybar >/dev/null 2>&1; then
  WAYBAR_CONFIG="$AURORA/waybar/config.jsonc"
  WAYBAR_STYLE="$AURORA/waybar/style.css"
  if [[ -r "$WAYBAR_CONFIG" ]]; then
    waybar -c "$WAYBAR_CONFIG" -s "$WAYBAR_STYLE" >/tmp/aurora-waybar.log 2>&1 &
    log "Waybar started"
  fi
fi

if command -v mako >/dev/null 2>&1; then
  mako >/tmp/aurora-mako.log 2>&1 &
fi

# Give the user a real terminal immediately. The launcher and existing
# Chimera shell remain available from the panel/menu and keyboard shortcuts.
if command -v foot >/dev/null 2>&1; then
  foot --app-id=aurora-terminal >/tmp/aurora-terminal.log 2>&1 &
elif [[ -x "$ROOT/aurora/emulators/bin/aurora-emulator-window.sh" ]]; then
  log "foot unavailable; no terminal autostart"
fi

log "desktop clients initialized; WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} DISPLAY=${DISPLAY:-unset}"
