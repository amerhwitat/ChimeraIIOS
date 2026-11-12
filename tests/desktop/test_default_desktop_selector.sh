#!/usr/bin/env bash
set -Eeuo pipefail
root="$(mktemp -d)"
trap 'rm -rf "$root"' EXIT
export HOME="$root/home"
mkdir -p "$HOME"
bash tools/desktop/set-default-desktop.sh freewin11
grep -qx 'default_desktop=freewin11' "$HOME/.config/chimera/desktop.conf"
bash tools/desktop/set-default-desktop.sh freexp
grep -qx 'default_desktop=freexp' "$HOME/.config/chimera/desktop.conf"
if bash tools/desktop/set-default-desktop.sh invalid; then
  echo "invalid desktop was accepted" >&2
  exit 1
fi
echo "default desktop selector tests passed"
