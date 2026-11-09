#!/usr/bin/env bash

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Aurora Shell Center

Usage:
  aurora-shell-center [shell-id|binary]
  aurora-shell-center              # interactive selection
  aurora-shell-center --list       # list installed shells
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
manifest="${CHIMERA_SHELL_MANIFEST:-/usr/share/chimera/aurora/shells-installed.tsv}"
resolve_shell() {
  local requested="$1" id binary
  [[ -r "$manifest" ]] || return 1
  while IFS='|' read -r id binary; do
    [[ -n "$id" && -n "$binary" ]] || continue
    if [[ "$requested" == "$id" || "$requested" == "$binary" ]]; then
      command -v "$binary" >/dev/null 2>&1 || return 1
      printf '%s\n' "$binary"
      return 0
    fi
  done < "$manifest"
  return 1
}
if [[ "${1:-}" == "--list" ]]; then
  [[ -r "$manifest" ]] && cat "$manifest" || exit 1
  exit 0
fi
if [[ $# -gt 0 ]]; then
  shell="$(resolve_shell "$1")" || { echo "Shell is not installed or not registered: $1" >&2; exit 127; }
  shift
  exec "$shell" "$@"
fi
if [[ ! -t 0 || ! -r "$manifest" ]]; then
  exec bash
fi
mapfile -t entries < <(cat "$manifest")
(("${#entries[@]}")) || exec bash
printf 'Aurora Shell Center — installed shells\n'
for i in "${!entries[@]}"; do
  IFS='|' read -r id binary <<< "${entries[$i]}"
  printf ' %2d) %s (%s)\n' "$((i+1))" "$id" "$binary"
done
read -r -p "Select shell [1-${#entries[@]}] (default 1): " choice
choice="${choice:-1}"
[[ "$choice" =~ ^[0-9]+$ ]] && ((choice>=1 && choice<=${#entries[@]})) || { echo "Invalid selection." >&2; exit 2; }
IFS='|' read -r id binary <<< "${entries[$((choice-1))]}"
command -v "$binary" >/dev/null 2>&1 || { echo "Shell executable disappeared: $binary" >&2; exit 127; }
exec "$binary"
