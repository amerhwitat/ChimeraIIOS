#!/usr/bin/env bash
set -Eeuo pipefail
desktop="${1:-}"
case "$desktop" in
  aurora|marine|freexp|freewin11|nebula) ;;
  *)
    echo "Usage: $0 {aurora|marine|freexp|freewin11|nebula}" >&2
    exit 64
    ;;
esac
config_root="${XDG_CONFIG_HOME:-${HOME:?HOME must be set}/.config}"
config_dir="$config_root/chimera"
mkdir -p "$config_dir"
tmp="$(mktemp "$config_dir/desktop.conf.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
printf 'default_desktop=%s\n' "$desktop" > "$tmp"
chmod 600 "$tmp"
mv -f "$tmp" "$config_dir/desktop.conf"
trap - EXIT
printf 'Default desktop set to %s\n' "$desktop"
