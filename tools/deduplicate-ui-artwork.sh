#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/deduplicate-ui-artwork.sh

Usage:
  tools/deduplicate-ui-artwork.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

# Safe artwork/UI deduplication. Boot-critical payloads are deliberately not
# touched. Canonical artwork lives under desktop/aurora/assets when possible.
ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
changed=0

is_asset() {
  case "$1" in
    *.png|*.jpg|*.jpeg|*.webp|*.gif|*.svg|*.ico|*.bmp|*.tif|*.tiff|*.wav|*.ogg|*.flac|*.mp3|*.ttf|*.otf|*.woff|*.woff2|*.css) return 0;;
    *) return 1;;
  esac
}

canonical_score() {
  case "$1" in
    */desktop/aurora/assets/*) echo "0:$1";;
    */desktop/aurora/*) echo "1:$1";;
    */assets/*) echo "2:$1";;
    */installer/*) echo "3:$1";;
    */recovery/*) echo "4:$1";;
    */mobile/*) echo "5:$1";;
    *) echo "9:$1";;
  esac
}

declare -A groups=()
while IFS= read -r -d '' f; do
  [[ -L "$f" || ! -s "$f" ]] && continue
  is_asset "$f" || continue
  key="$(stat -c '%s' "$f")-$(sha256sum "$f" | awk '{print $1}')"
  groups["$key"]+=$'\n'"$f"
done < <(find "$ROOT" -type d \( -name .git -o -name build -o -name chimera-build -o -name chimera-output -o -name node_modules \) -prune -o -type f -print0)

for key in "${!groups[@]}"; do
  mapfile -t files < <(printf '%s\n' "${groups[$key]}" | sed '/^$/d')
  (( ${#files[@]} > 1 )) || continue
  canonical="$(printf '%s\n' "${files[@]}" | while read -r f; do canonical_score "$f"; done | sort | head -n1 | cut -d: -f2-)"
  for f in "${files[@]}"; do
    [[ "$f" == "$canonical" ]] && continue
    rel="$(python3 - "$f" "$canonical" <<'PY'
import os,sys
p,c=sys.argv[1:]
print(os.path.relpath(c, os.path.dirname(p)))
PY
)"
    rm -f -- "$f"
    ln -s -- "$rel" "$f"
    printf 'ARTWORK_LINK %s -> %s\n' "${f#$ROOT/}" "$rel"
    changed=1
done
done

printf 'ARTWORK_DEDUP changed=%s\n' "$changed"
