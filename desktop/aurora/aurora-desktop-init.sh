#!/usr/bin/env bash
set -euo pipefail

ROOT=/usr/share/chimera
AURORA="$ROOT/aurora"
LOG_DIR="${XDG_RUNTIME_DIR:-/tmp}/chimera"
mkdir -p "$LOG_DIR"
log(){ printf '[Aurora] %s\n' "$*" >> "$LOG_DIR/aurora-desktop.log"; }
export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-Aurora}"
export XDG_SESSION_DESKTOP="${XDG_SESSION_DESKTOP:-Aurora}"
export XDG_SESSION_TYPE=wayland
if command -v dbus-update-activation-environment >/dev/null 2>&1; then
  dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XDG_RUNTIME_DIR 2>/dev/null || true
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-system-running >/dev/null 2>&1; then
  systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE XDG_RUNTIME_DIR 2>/dev/null || true
  systemctl --user start graphical-session.target 2>/dev/null || true
fi
if command -v pipewire >/dev/null 2>&1 && ! pgrep -u "$(id -u)" -x pipewire >/dev/null 2>&1; then
  pipewire >/tmp/aurora-pipewire.log 2>&1 &
fi
if command -v wireplumber >/dev/null 2>&1 && ! pgrep -u "$(id -u)" -x wireplumber >/dev/null 2>&1; then
  wireplumber >/tmp/aurora-wireplumber.log 2>&1 &
fi

# Optional initialization video. It is launched only after Wayland is ready and
# never blocks the desktop if video playback is unavailable.
if [[ -f "$AURORA/aurora-init-splash.sh" ]]; then
  CHIMERA_INIT_VIDEO="${CHIMERA_INIT_VIDEO:-$AURORA/assets/init.mp4}" \
    CHIMERA_PROGRESS_FILE="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}" \
    bash "$AURORA/aurora-init-splash.sh" >/tmp/aurora-init-splash.log 2>&1 &
fi

if command -v swaybg >/dev/null 2>&1; then
  bg="${CHIMERA_AURORA_BACKGROUND:-$AURORA/aurora-wayland-glass.png}"
  if [[ -r "$bg" ]]; then
    swaybg -m fill -i "$bg" >/tmp/aurora-swaybg.log 2>&1 &
    log "background started: $bg"
  else
    log "background asset unavailable: $bg"
  fi
fi
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
if command -v foot >/dev/null 2>&1; then
  foot --app-id=aurora-terminal >/tmp/aurora-terminal.log 2>&1 &
elif command -v alacritty >/dev/null 2>&1; then
  alacritty --class aurora-terminal >/tmp/aurora-terminal.log 2>&1 &
elif command -v kitty >/dev/null 2>&1; then
  kitty --class aurora-terminal >/tmp/aurora-terminal.log 2>&1 &
elif command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal >/tmp/aurora-terminal.log 2>&1 &
elif command -v konsole >/dev/null 2>&1; then
  konsole >/tmp/aurora-terminal.log 2>&1 &
else
  log "no graphical terminal executable found"
fi
launch_queued_emulator(){
  local q="${CHIMERA_EMULATOR_QUEUE_DIR:-$XDG_RUNTIME_DIR/chimera/emulators}"
  local id launcher arg=""
  [[ -s "$q/pending" ]] || return 0
  id="$(cat "$q/pending")"
  case "$id" in
    sakhr-ax170) launcher="$AURORA/emulators/bin/launch-sakhr-ax170.sh" ;;
    sakhr-ax230) launcher="$AURORA/emulators/bin/launch-sakhr-ax230.sh" ;;
    retro-*) launcher="$AURORA/emulators/bin/launch-retro.sh"; arg="$id" ;;
    *) log "unknown queued emulator: $id"; return 0 ;;
  esac
  [[ -x "$launcher" ]] || { log "emulator launcher missing: $launcher"; return 0; }
  mv "$q/pending" "$q/active" 2>/dev/null || return 0
  if [[ -n "$arg" ]]; then
    "$launcher" "$arg" >>"$LOG_DIR/aurora-emulator.log" 2>&1 &
  else
    "$launcher" >>"$LOG_DIR/aurora-emulator.log" 2>&1 &
  fi
  rm -f "$q/active" "$q/title" "$q/args"
}
for _ in $(seq 1 20); do
  if [[ -s "${CHIMERA_EMULATOR_QUEUE_DIR:-$XDG_RUNTIME_DIR/chimera/emulators}/pending" ]] && [[ -n "${WAYLAND_DISPLAY:-}" ]] && [[ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
    launch_queued_emulator
    break
  fi
  sleep 1
done
log "desktop clients initialized; WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} DISPLAY=${DISPLAY:-unset}"
