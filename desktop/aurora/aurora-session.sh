#!/bin/sh
set -eu

RUNTIME_DIR="${CHIMERA_RUNTIME_DIR:-/run/chimera}"
READY_FILE="$RUNTIME_DIR/kernel.ready"

if [ ! -r "$READY_FILE" ]; then
    echo "Aurora: Chimera kernel runtime is not ready: $READY_FILE" >&2
    exit 1
fi

# Prefer a future native Aurora compositor, then well-known Wayland compositors.
# The fallback keeps the boot path usable on ordinary Linux installations while
# Aurora's native compositor is still a research component.
if [ -n "${AURORA_COMPOSITOR:-}" ]; then
    COMPOSITOR="$AURORA_COMPOSITOR"
elif command -v aurora-compositor >/dev/null 2>&1; then
    COMPOSITOR="aurora-compositor"
elif command -v sway >/dev/null 2>&1; then
    COMPOSITOR="sway"
elif command -v weston >/dev/null 2>&1; then
    COMPOSITOR="weston"
elif command -v labwc >/dev/null 2>&1; then
    COMPOSITOR="labwc"
elif command -v kwin_wayland >/dev/null 2>&1; then
    COMPOSITOR="kwin_wayland"
else
    echo "Aurora: no Wayland compositor installed. Install Aurora or a supported fallback." >&2
    exit 1
fi

export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-Aurora}"
export XDG_SESSION_DESKTOP="${XDG_SESSION_DESKTOP:-aurora}"
export MOZ_ENABLE_WAYLAND="${MOZ_ENABLE_WAYLAND:-1}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland}"
export GDK_BACKEND="${GDK_BACKEND:-wayland,x11}"

exec "$COMPOSITOR" "$@"
