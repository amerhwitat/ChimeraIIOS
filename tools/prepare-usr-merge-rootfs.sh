#!/usr/bin/env bash
# Enforce usr-merge layout for a staged Chimera root filesystem.
# Real files in legacy /bin and /sbin are moved into /usr; conflicting files
# fail closed rather than silently overwriting one implementation.
set -Eeuo pipefail

ROOTFS="${CHIMERA_ROOTFS_DIR:-${1:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../rootfs" && pwd)}}"
mkdir -p "$ROOTFS/usr/bin" "$ROOTFS/usr/sbin"

merge_legacy_dir() {
  local legacy="$1" canonical="$2" link_target="$3" entry name
  if [[ -L "$legacy" ]]; then
    local target
    target="$(readlink "$legacy")"
    [[ "$target" == "$link_target" ]] || {
      echo "usr-merge: refusing unexpected symlink $legacy -> $target (expected $link_target)" >&2
      return 1
    }
    return 0
  fi
  if [[ -e "$legacy" && ! -d "$legacy" ]]; then
    echo "usr-merge: refusing non-directory path: $legacy" >&2
    return 1
  fi
  if [[ -d "$legacy" ]]; then
    shopt -s dotglob nullglob
    for entry in "$legacy"/*; do
      [[ -e "$entry" || -L "$entry" ]] || continue
      name="${entry##*/}"
      if [[ -e "$canonical/$name" || -L "$canonical/$name" ]]; then
        if [[ -f "$entry" && -f "$canonical/$name" ]] && cmp -s -- "$entry" "$canonical/$name"; then
          rm -- "$entry"
        else
          echo "usr-merge: collision at $canonical/$name; refusing to overwrite" >&2
          return 1
        fi
      else
        mv -- "$entry" "$canonical/$name"
      fi
    done
    rmdir "$legacy"
  fi
  ln -s "$link_target" "$legacy"
}

merge_legacy_dir "$ROOTFS/bin" "$ROOTFS/usr/bin" "/usr/bin"
merge_legacy_dir "$ROOTFS/sbin" "$ROOTFS/usr/sbin" "/usr/sbin"

[[ -L "$ROOTFS/bin" && "$(readlink "$ROOTFS/bin")" == "/usr/bin" ]]
[[ -L "$ROOTFS/sbin" && "$(readlink "$ROOTFS/sbin")" == "/usr/sbin" ]]
printf 'usr-merge rootfs layout verified: %s\n' "$ROOTFS"
