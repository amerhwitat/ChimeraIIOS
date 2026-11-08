#!/bin/sh
set -eu

# WSL2 exposes Windows volumes through DrvFs (normally /mnt/c, /mnt/d, ...).
# Publish stable, explicit aliases under /mnt/drive/<letter> without mounting
# the same volume twice or changing WSL's native automount configuration.
MNT_ROOT=${CHIMERA_WSL_MNT_ROOT:-/mnt}
DRIVE_ROOT=${CHIMERA_WSL_DRIVE_ROOT:-$MNT_ROOT/drive}

is_wsl() {
  grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease 2>/dev/null ||
    grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null ||
    [ -n "${WSL_INTEROP:-}" ] ||
    [ -d /mnt/wsl ]
}

if ! is_wsl; then
  echo "[WSL][INFO] Not running under WSL; Windows drive aliases were not created."
  exit 0
fi

if ! command -v findmnt >/dev/null 2>&1; then
  echo "[WSL][ERROR] findmnt is required to identify mounted DrvFs volumes." >&2
  exit 1
fi

mkdir -p "$DRIVE_ROOT"
mapped=0
while IFS=' ' read -r source target; do
  [ -n "${source:-}" ] && [ -n "${target:-}" ] || continue
  case "$source" in
    [A-Za-z]:*) letter=$(printf '%s' "$source" | cut -c1 | tr '[:upper:]' '[:lower:]') ;;
    *) continue ;;
  esac
  fstype=$(findmnt -rn -M "$target" -o FSTYPE 2>/dev/null | head -n 1 || true)
  [ "$fstype" = "drvfs" ] || continue
  [ -d "$target" ] || continue

  for alias in "$letter" "$(printf '%s' "$letter" | tr '[:lower:]' '[:upper:]')"; do
    link="$DRIVE_ROOT/$alias"
    if [ -e "$link" ] && [ ! -L "$link" ]; then
      echo "[WSL][WARN] Preserving existing non-symlink path: $link" >&2
      continue
    fi
    tmp="$DRIVE_ROOT/.$alias.$$"
    rm -f "$tmp"
    ln -s "$target" "$tmp"
    mv -f "$tmp" "$link"
  done
  echo "[WSL] $source -> $DRIVE_ROOT/$letter ($target)"
  mapped=$((mapped + 1))
done <<EOF
$(findmnt -rn -t drvfs -o SOURCE,TARGET 2>/dev/null || true)
EOF

if [ "$mapped" -eq 0 ]; then
  echo "[WSL][INFO] No mounted DrvFs drive letters were found; /mnt/drive is ready for later refresh."
else
  echo "[WSL] Published $mapped Windows drive mapping(s) under $DRIVE_ROOT."
fi
