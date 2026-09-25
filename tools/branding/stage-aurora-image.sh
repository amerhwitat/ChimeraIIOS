#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${CHIMERA_AURORA_ASSET:-}"
for candidate in "${OUT:-}" "$ROOT/assets/Aurora-Wayland-Glass-Desktop.png" "$ROOT/assets/aurora/Aurora-Wayland-Glass-Desktop.png" "$ROOT/Aurora-Wayland-Glass-Desktop.png"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then OUT="$candidate"; break; fi
done
if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then echo "[Chimera][AURORA] External image not found; SVG fallback remains active."; exit 0; fi
ISO="${1:?ISO staging directory required}"
mkdir -p "$ISO/boot/grub" "$ISO/boot/jasper" "$ISO/boot/spitfire" "$ISO/install" "$ISO/desktop/aurora"
for dst in "$ISO/boot/grub/aurora-wayland-glass.png" "$ISO/boot/jasper/background.png" "$ISO/boot/spitfire/background.png" "$ISO/install/installer-background.png" "$ISO/install/library-background.png" "$ISO/desktop/aurora/aurora-wayland-glass.png"; do cp "$OUT" "$dst"; done
echo "[Chimera][AURORA] Applied supplied artwork to all boot, installer and desktop surfaces."
