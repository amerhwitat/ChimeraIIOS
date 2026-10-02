#!/usr/bin/env bash
set -euo pipefail

ROOT=/usr/share/chimera
AURORA="$ROOT/aurora"
USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/labwc"

mkdir -p "$USER_CONFIG"

# Install the controlled Aurora labwc configuration only when the user has not
# customized it. This preserves user changes across subsequent sessions.
for f in rc.xml menu.xml environment autostart; do
  src="$AURORA/labwc/$f"
  dst="$USER_CONFIG/$f"
  if [[ -r "$src" && ! -e "$dst" ]]; then
    cp -f "$src" "$dst"
  fi
done

export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=Aurora
export XDG_SESSION_DESKTOP=Aurora
export GDK_BACKEND="${GDK_BACKEND:-wayland,x11}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland;xcb}"
export MOZ_ENABLE_WAYLAND="${MOZ_ENABLE_WAYLAND:-1}"
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-wayland,x11}"
export CHIMERA_AURORA_BACKGROUND="${CHIMERA_AURORA_BACKGROUND:-$AURORA/ChimeraIIOS-Aurora-Wayland-Glass.jpg}"

if [[ -z "${XDG_RUNTIME_DIR:-}" ]]; then
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR" 2>/dev/null || true

# dbus-run-session gives desktop portals, settings services and media/session
# clients a real per-login D-Bus bus when the user session is not already
# providing one. labwc -S owns the graphical session and terminates when the
# session client exits.
if command -v labwc >/dev/null 2>&1; then
  if command -v dbus-run-session >/dev/null 2>&1 && [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    exec dbus-run-session -- labwc -C "$USER_CONFIG" -S "$AURORA/aurora-desktop-init.sh"
  fi
  exec labwc -C "$USER_CONFIG" -S "$AURORA/aurora-desktop-init.sh"
fi

printf '%s\n' '[Aurora][ERROR] No Wayland compositor (labwc) is installed.' >&2
printf '%s\n' '[Aurora][INFO] Falling back to the Chimera interactive shell.' >&2
if [[ -x "$ROOT/../userland/shell/chimera-shell" ]]; then
  exec "$ROOT/../userland/shell/chimera-shell" -i
fi
exec "${SHELL:-/bin/bash}" -i
