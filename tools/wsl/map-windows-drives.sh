#!/usr/bin/env bash
# Create WSL-style /mnt/drive/C aliases for Windows drives already mounted by WSL.
# This is a host-side convenience adapter; it does not implement NTFS in Koronos.
set -Eeuo pipefail

WSL_MNT_ROOT="${CHIMERA_WSL_MNT_ROOT:-/mnt}"
DRIVE_ROOT="${CHIMERA_WINDOWS_DRIVE_ROOT:-/mnt/drive}"
DRY_RUN="${CHIMERA_WSL_DRIVE_DRY_RUN:-0}"
ALLOW_UNVERIFIED="${CHIMERA_WSL_DRIVE_ALLOW_UNVERIFIED:-0}"

is_wsl() {
  [[ "${CHIMERA_FORCE_WSL:-0}" == 1 ]] && return 0
  [[ -n "${WSL_INTEROP:-}" ]] && return 0
  grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null
}

if ! is_wsl; then
  echo "[wsl-drive] not running inside WSL; no drive aliases created" >&2
  exit 2
fi
[[ -d "$WSL_MNT_ROOT" ]] || { echo "[wsl-drive] mount root not found: $WSL_MNT_ROOT" >&2; exit 2; }

if [[ "$DRY_RUN" != 1 ]]; then
  mkdir -p -- "$DRIVE_ROOT"
fi

mapped=0
skipped=0
for source in "$WSL_MNT_ROOT"/[a-z]; do
  [[ -d "$source" ]] || continue
  letter="${source##*/}"
  target="$DRIVE_ROOT/${letter^^}"

  # Only alias actual mounted Windows drives. WSL commonly reports drvfs;
  # some WSL2 configurations expose the Windows 9p transport instead.
  fstype=""
  if command -v findmnt >/dev/null 2>&1; then
    fstype="$(findmnt -T "$source" -n -o FSTYPE 2>/dev/null | head -n 1 || true)"
  fi
  if [[ "$ALLOW_UNVERIFIED" != 1 && "$fstype" != drvfs && "$fstype" != 9p ]]; then
    echo "[wsl-drive] skip /$letter: filesystem is not verified as DrvFs/9p (type='${fstype:-unknown}')" >&2
    skipped=$((skipped + 1))
    continue
  fi

  if [[ -L "$target" ]]; then
    current="$(readlink -f -- "$target" 2>/dev/null || true)"
    actual="$(readlink -f -- "$source" 2>/dev/null || true)"
    if [[ -n "$actual" && "$current" == "$actual" ]]; then
      echo "[wsl-drive] already mapped $target -> $source"
      mapped=$((mapped + 1))
      continue
    fi
    echo "[wsl-drive] refusing to replace existing symlink: $target" >&2
    skipped=$((skipped + 1))
    continue
  fi
  if [[ -e "$target" ]]; then
    echo "[wsl-drive] refusing to overwrite existing path: $target" >&2
    skipped=$((skipped + 1))
    continue
  fi

  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[wsl-drive] would map $target -> $source"
  else
    ln -s -- "$source" "$target"
    echo "[wsl-drive] mapped $target -> $source"
  fi
  mapped=$((mapped + 1))
done

printf '[wsl-drive] complete: mapped=%d skipped=%d root=%s\n' "$mapped" "$skipped" "$DRIVE_ROOT"
