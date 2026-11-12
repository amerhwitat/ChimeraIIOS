#!/usr/bin/env bash
set -euo pipefail

config_file="${XDG_CONFIG_HOME:-${HOME:-/tmp}/.config}/chimera/desktop.conf"
configured="aurora"
if [[ -r "$config_file" ]]; then
  while IFS='=' read -r key value; do
    if [[ "$key" == "default_desktop" ]]; then configured="$value"; fi
  done < "$config_file"
fi
desktop="${1:-${CHIMERA_DEFAULT_DESKTOP:-$configured}}"
case "$desktop" in
  aurora|marine|freexp|freewin11) ;;
  *)
    echo "Usage: $0 {aurora|marine|freexp|freewin11}" >&2
    exit 64
    ;;
esac

for command_name in Xorg xinit; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "[Chimera][X11][ERROR] required provider missing: $command_name" >&2
    exit 127
  fi
done

shell_bin="${CHIMERA_DESKTOP_SHELL:-/usr/bin/chimera-desktop-shell}"
if [[ ! -x "$shell_bin" ]]; then
  echo "[Chimera][X11][ERROR] native desktop shell not found: $shell_bin" >&2
  exit 127
fi

if [[ "${CHIMERA_X11_RUNTIME_VERIFIED:-0}" != "1" && "${CHIMERA_X11_FORCE_UNVERIFIED:-0}" != "1" ]]; then
  echo "[Chimera][X11][BLOCKED] Koronos X11/DRM/VT/Linux-ABI runtime has not passed acceptance." >&2
  echo "Set CHIMERA_X11_FORCE_UNVERIFIED=1 only for controlled development testing." >&2
  exit 78
fi

exec xinit "$shell_bin" "--desktop=$desktop" -- Xorg :0 vt1 -keeptty -nolisten tcp
