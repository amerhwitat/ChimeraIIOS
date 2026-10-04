#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/link-runtime-assets.sh

Usage:
  tools/link-runtime-assets.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

# Link an already-canonical runtime tree into a staging tree without making
# another physical copy when the filesystem permits it.
#
# auto  = hard-link when possible, otherwise copy
# hard  = require hard-links
# soft  = create relative symbolic links
# copy  = conventional copies

SRC=""
DST=""
MODE="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SRC="$2"; shift 2 ;;
    --dest) DST="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$SRC" && -n "$DST" ]] || {
  echo 'usage: link-runtime-assets.sh --source DIR --dest DIR [--mode auto|hard|soft|copy]' >&2
  exit 2
}
[[ "$MODE" =~ ^(auto|hard|soft|copy)$ ]] || {
  echo "Invalid mode: $MODE" >&2
  exit 2
}

SRC="$(cd "$SRC" && pwd)"
mkdir -p "$DST"
DST="$(cd "$DST" && pwd)"

while IFS= read -r -d '' f; do
  rel="${f#$SRC/}"
  out="$DST/$rel"
  mkdir -p "$(dirname "$out")"
  [[ -e "$out" || -L "$out" ]] && continue

  if [[ "$MODE" == soft ]]; then
    ln -s "$(realpath --relative-to="$(dirname "$out")" "$f")" "$out"
    continue
  fi

  if [[ "$MODE" == hard || "$MODE" == auto ]]; then
    if ln "$f" "$out" 2>/dev/null; then
      continue
    fi
    [[ "$MODE" == hard ]] && {
      echo "Cannot hard-link $rel; source and destination may be on different filesystems" >&2
      exit 1
    }
  fi

  cp -p -- "$f" "$out"
done < <(find "$SRC" -type f -print0)
