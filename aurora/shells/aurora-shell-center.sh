#!/usr/bin/env bash
set -Eeuo pipefail
manifest=/usr/share/chimera/aurora/terminal-shell-installed.tsv
[[ -s "$manifest" ]] || { echo "No verified shell providers are installed." >&2; exit 1; }
mapfile -t entries < <(while IFS='|' read -r pkg bin; do
  case "$bin" in bash|zsh|fish|dash|mksh|yash|elvish|nu) printf '%s|%s\n' "$pkg" "$bin";; esac
done < "$manifest")
(("${#entries[@]}")) || { echo "No alternative shell is installed." >&2; exit 1; }
printf 'Aurora Shell Center\n'
for i in "${!entries[@]}"; do printf ' %2d) %s\n' "$((i+1))" "${entries[$i]#*|}"; done
read -r -p "Select shell [1-${#entries[@]}]: " choice
[[ "$choice" =~ ^[0-9]+$ ]] && ((choice>=1 && choice<=${#entries[@]})) || { echo "Invalid selection." >&2; exit 2; }
bin="${entries[$((choice-1))]#*|}"
exec "$bin" -i
