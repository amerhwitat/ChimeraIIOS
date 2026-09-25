#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${CHIMERA_AURORA_ASSET:-}"
for candidate in "${OUT:-}" "$ROOT/assets/Aurora-Wayland-Glass-Desktop.png" "$ROOT/assets/aurora/Aurora-Wayland-Glass-Desktop.png" "$ROOT/Aurora-Wayland-Glass-Desktop.png"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then OUT="$candidate"; break; fi
done
EMBEDDED="$ROOT/system/branding/aurora-default.jpg.base64"
if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  if [ -s "$EMBEDDED" ] && command -v base64 >/dev/null 2>&1; then
    mkdir -p "$ROOT/build/branding"
    base64 -d "$EMBEDDED" > "$ROOT/build/branding/aurora-default.jpg"
    OUT="$ROOT/build/branding/aurora-default.jpg"
    echo "[Chimera][AURORA] Using embedded offline Aurora default artwork."
  else
    echo "[Chimera][AURORA] External image not found; SVG fallback remains active."
    exit 0
  fi
fi
ISO="${1:?ISO staging directory required}"
mkdir -p "$ISO/boot/grub" "$ISO/boot/jasper" "$ISO/boot/spitfire" "$ISO/install" "$ISO/desktop/aurora"
for dst in "$ISO/boot/grub/aurora-wayland-glass.png" "$ISO/boot/jasper/background.png" "$ISO/boot/spitfire/background.png" "$ISO/install/installer-background.png" "$ISO/install/library-background.png" "$ISO/desktop/aurora/aurora-wayland-glass.png"; do cp "$OUT" "$dst"; done
echo "[Chimera][AURORA] Applied supplied artwork to all boot, installer and desktop surfaces."
