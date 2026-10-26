#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-desktop-init.sh

Usage:
  desktop/aurora/aurora-desktop-init.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

ROOT=/usr/share/chimera
AURORA="$ROOT/aurora"
LOG_DIR="${XDG_RUNTIME_DIR:-/tmp}/chimera"
mkdir -p "$LOG_DIR"
log(){ printf '[Aurora] %s\n' "$*" >> "$LOG_DIR/aurora-desktop.log"; }

# Event-driven UI progress: only advance after a real session/service check.
PROGRESS_STATE="${CHIMERA_PROGRESS_FILE:-/run/chimera/koronos-progress.state}"
progress_set(){
  local pct="$1" phase="$2" message="$3" tmp seq
  [[ "$pct" =~ ^[0-9]+$ && "$pct" -ge 0 && "$pct" -le 100 ]] || return 2
  [[ -n "$phase" && -n "$message" ]] || return 2
  local state_dir
  state_dir="$(dirname "$PROGRESS_STATE")"
  if ! mkdir -p "$state_dir" 2>/dev/null || [[ ! -w "$state_dir" ]]; then
    # A user session may not have write access to the root-owned boot state.
    # Fall back only when the caller did not explicitly choose a shared path.
    if [[ -z "${CHIMERA_PROGRESS_FILE:-}" && -n "${XDG_RUNTIME_DIR:-}" ]]; then
      PROGRESS_STATE="$XDG_RUNTIME_DIR/chimera/koronos-progress.state"
      state_dir="$(dirname "$PROGRESS_STATE")"
      mkdir -p "$state_dir" 2>/dev/null || return 0
      [[ -w "$state_dir" ]] || return 0
    else
      return 0
    fi
  fi
  seq="$(date +%s%N 2>/dev/null || date +%s)"
  tmp="$PROGRESS_STATE.tmp.$$"
  if printf 'version=1\nsequence=%s\npercent=%s\nphase=%s\nmessage=%s\ntimestamp=%s\n' \
      "$seq" "$pct" "$phase" "$message" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$tmp"; then
    mv -f "$tmp" "$PROGRESS_STATE" || { rm -f "$tmp"; return 1; }
  else
    rm -f "$tmp"; return 1
  fi
}
wayland_socket_ready(){
  [[ -n "${WAYLAND_DISPLAY:-}" && -n "${XDG_RUNTIME_DIR:-}" &&
     -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]
}
compositor_process_alive(){
  command -v pgrep >/dev/null 2>&1 &&
    pgrep -u "$(id -u)" -f '(^|/)(sway|weston|kwin_wayland|wayfire|labwc|cage)( |$)' >/dev/null 2>&1
}
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

# The milestone is based on the actual Wayland socket, not elapsed time.
progress_set 80 aurora-session "Aurora session environment exported" || true
for _ in $(seq 1 10); do
  wayland_socket_ready && break
  sleep 1
done
if wayland_socket_ready; then
  progress_set 90 wayland-session "Wayland session socket is available" || true
  if command -v zenity >/dev/null 2>&1 && [[ -x "$AURORA/aurora-progress.sh" ]]; then
    CHIMERA_PROGRESS_FILE="$PROGRESS_STATE" "$AURORA/aurora-progress.sh" gui >/tmp/aurora-progress-ui.log 2>&1 &
  fi
else
  progress_set 85 wayland-session "Waiting for a verified Wayland session socket" || true
  log "Wayland session socket unavailable; refusing to report desktop readiness"
fi

# Select the video first, then always invoke the launcher. The old '||' chain
# accidentally skipped playback whenever the primary Init.mp4 already existed.
if [[ -f "$AURORA/aurora-init-splash.sh" ]]; then
  CHIMERA_INIT_VIDEO="${CHIMERA_INIT_VIDEO:-$AURORA/assets/Init.mp4}"
  [[ -s "$CHIMERA_INIT_VIDEO" ]] || CHIMERA_INIT_VIDEO="$AURORA/assets/init.mp4"
  if [[ -s "$CHIMERA_INIT_VIDEO" ]]; then
    CHIMERA_INIT_VIDEO="$CHIMERA_INIT_VIDEO" CHIMERA_PROGRESS_FILE="$PROGRESS_STATE" \
      bash "$AURORA/aurora-init-splash.sh" >/tmp/aurora-init-splash.log 2>&1 &
  else
    log "Init.mp4 unavailable; continuing without the optional splash video"
  fi
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
log "desktop client launch phase finished; WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-unset} DISPLAY=${DISPLAY:-unset}"
if wayland_socket_ready && compositor_process_alive; then
  progress_set 100 aurora-session "Aurora desktop session initialized; kernel and service acceptance remain separate" || true
  log "verified Wayland socket and compositor process; desktop session milestone complete"
elif wayland_socket_ready; then
  progress_set 95 aurora-session "Wayland socket exists but compositor process health was not confirmed" || true
  log "Wayland socket exists but compositor process health was not confirmed"
else
  progress_set 85 aurora-session "Desktop startup incomplete: Wayland socket unavailable" || true
  log "desktop readiness withheld because the Wayland socket is unavailable"
fi
