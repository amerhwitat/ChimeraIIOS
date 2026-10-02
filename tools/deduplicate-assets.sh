#!/usr/bin/env bash
set -Eeuo pipefail

# Chimera II OS asset deduplicator.
#
# Git stores symlinks natively, but cannot preserve hard-link relationships in a
# portable clone. Therefore repository-level deduplication uses relative
# symbolic links. Runtime/build staging may materialize those links or replace
# them with hard links when the source and destination share a filesystem.
#
# Default mode aliases duplicate binary/static runtime assets. --all also
# considers source/text files; use it only when intentionally normalizing a
# repository-wide tree.

ROOT="${CHIMERA_DEDUP_ROOT:-.}"
DRY_RUN=0
ALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --all) ALL=1; shift ;;
    --runtime) ALL=0; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$ROOT" && pwd)"

EXCLUDES=(
  .git build chimera-build chimera-output node_modules dist out tmp
)

prune_expr=()
for e in "${EXCLUDES[@]}"; do
  prune_expr+=( -name "$e" -o )
done
unset 'prune_expr[${#prune_expr[@]}-1]'

find_args=("$ROOT" -type d \( "${prune_expr[@]}" \) -prune -o -type f -print0)

if (( ALL == 0 )); then
  # Artwork, audio, fonts, firmware, boot images and other runtime payloads.
  find_args=("$ROOT" -type d \( "${prune_expr[@]}" \) -prune -o -type f \( \
    -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o \
    -iname '*.gif' -o -iname '*.svg' -o -iname '*.ico' -o -iname '*.bmp' -o \
    -iname '*.tif' -o -iname '*.tiff' -o -iname '*.wav' -o -iname '*.ogg' -o \
    -iname '*.flac' -o -iname '*.mp3' -o -iname '*.ttf' -o -iname '*.otf' -o \
    -iname '*.woff' -o -iname '*.woff2' -o -iname '*.bin' -o -iname '*.img' -o \
    -iname '*.efi' -o -iname '*.rom' -o -iname '*.qcow2' -o -iname '*.iso' -o \
    -iname '*.squashfs' -o -iname '*.cpio' -o -iname '*.lz4' -o -iname '*.zst' \
  \) -print0)
fi

declare -A byhash=()
while IFS= read -r -d '' f; do
  [[ -L "$f" ]] && continue
  [[ -s "$f" ]] || continue
  size="$(stat -c '%s' "$f")"
  hash="$(sha256sum "$f" | awk '{print $1}')"
  key="$size:$hash"
  byhash["$key"]+=$'\n'"$f"
done < <(find "${find_args[@]}")

canonical_score() {
  local p="$1" score=1000
  case "$p" in
    */desktop/aurora/assets/*) score=0 ;;
    */desktop/aurora/*) score=10 ;;
    */assets/*) score=20 ;;
    */installer/*) score=30 ;;
    */recovery/*) score=40 ;;
    */mobile/*) score=50 ;;
    */boot/*) score=60 ;;
    */live/*) score=70 ;;
    *) score=100 ;;
  esac
  printf '%04d:%08d:%s\n' "$score" "${#p}" "$p"
}

changed=0
alias_count=0

for key in "${!byhash[@]}"; do
  mapfile -t paths < <(printf '%s\n' "${byhash[$key]}" | sed '/^$/d')
  (( ${#paths[@]} > 1 )) || continue

  canonical="$(printf '%s\n' "${paths[@]}" \
    | while IFS= read -r p; do canonical_score "$p"; done \
    | sort | head -n1 | cut -d: -f3-)"

  for p in "${paths[@]}"; do
    [[ "$p" == "$canonical" ]] && continue

    rel="$(python3 - "$p" "$canonical" <<'PY'
import os
import sys
p, canonical = sys.argv[1:]
print(os.path.relpath(canonical, os.path.dirname(p)))
PY
)"

    printf 'DEDUP %s -> %s\n' "${p#$ROOT/}" "$rel"
    (( DRY_RUN == 1 )) && continue

    rm -f -- "$p"
    ln -s -- "$rel" "$p"
    changed=1
    alias_count=$((alias_count + 1))
  done
done

mode=runtime
(( ALL == 1 )) && mode=all
printf 'DEDUP_RESULT changed=%s aliases=%s mode=%s\n' "$changed" "$alias_count" "$mode"
