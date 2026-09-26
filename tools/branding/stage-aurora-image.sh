#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${CHIMERA_AURORA_ASSET:-}"
# Search order deliberately keeps the user-provided artwork as the canonical default.
# The /mnt/data path is useful when this script is run in the same Linux/WSL
# environment that received the attached ChatGPT asset; repository assets remain
# the portable/offline source for normal clones.
for candidate in \
  "${OUT:-}" \
  "/mnt/data/Aurora-Wayland-Glass-Desktop.png.png" \
  "$ROOT/assets/Aurora-Wayland-Glass-Desktop.png" \
  "$ROOT/assets/aurora/Aurora-Wayland-Glass-Desktop.png" \
  "$ROOT/Aurora-Wayland-Glass-Desktop.png"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then OUT="$candidate"; break; fi
done
EMBEDDED="$ROOT/system/branding/aurora-default.jpg.base64"
EMBEDDED_PNG="$ROOT/system/branding/aurora-default.png.base64"
if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  if [ -s "$EMBEDDED_PNG" ] && command -v base64 >/dev/null 2>&1; then
    mkdir -p "$ROOT/build/branding"
    base64 -d "$EMBEDDED_PNG" > "$ROOT/build/branding/aurora-default.png"
    OUT="$ROOT/build/branding/aurora-default.png"
    echo "[Chimera][AURORA] Using embedded offline Aurora PNG artwork."
  elif [ -s "$EMBEDDED" ] && command -v base64 >/dev/null 2>&1; then
    mkdir -p "$ROOT/build/branding"
    base64 -d "$EMBEDDED" > "$ROOT/build/branding/aurora-default.jpg"
    OUT="$ROOT/build/branding/aurora-default.jpg"
    echo "[Chimera][AURORA] Using embedded offline Aurora fallback artwork."
  else
    echo "[Chimera][AURORA] External image not found; SVG fallback remains active."
    exit 0
  fi
fi
ISO="${1:?ISO staging directory required}"
ROOTFS="${CHIMERA_ROOTFS_DIR:-$ISO/rootfs}"
mkdir -p "$ISO/boot/grub" "$ISO/boot/jasper" "$ISO/boot/spitfire" "$ISO/install" "$ISO/desktop/aurora" "$ISO/desktop/aurora/backgrounds" "$ISO/system/branding" "$ISO/usr/share/backgrounds/chimera" "$ISO/usr/share/chimera/aurora" "$ISO/etc/chimera" "$ROOTFS/usr/share/backgrounds/chimera" "$ROOTFS_DIR/usr/share/chimera/aurora" "$ROOTFS_DIR/etc/chimera"
for dst in \
  "$ISO/boot/grub/aurora-wayland-glass.png" \
  "$ISO/boot/jasper/background.png" \
  "$ISO/boot/spitfire/background.png" \
  "$ISO/install/installer-background.png" \
  "$ISO/install/library-background.png" \
  "$ISO/desktop/aurora/aurora-wayland-glass.png" \
  "$ISO/desktop/aurora/backgrounds/Aurora-Wayland-Glass-Desktop.png" \
  "$ISO/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png" \
  "$ISO/usr/share/chimera/aurora/aurora-wayland-glass.png"; do
  cp "$OUT" "$dst"
done

# Mirror the canonical asset into the live/root filesystem as well as the ISO
# control tree, so Aurora can consume it after Koronos hands off to userland.
cp "$OUT" "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png"
cp "$OUT" "$ROOTFS_DIR/usr/share/chimera/aurora/aurora-wayland-glass.png"

# The background is a default, not a hard-coded runtime lock. Users/compositors
# can replace the path later through the system or per-user Chimera setting.
cat > "$ROOTFS_DIR/etc/chimera/desktop-background.conf" <<'EOF'
# Chimera II OS Aurora desktop background.
# Replace this path to change the desktop wallpaper without rebuilding the ISO.
CHIMERA_DESKTOP_BACKGROUND=/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png
CHIMERA_LOCKSCREEN_BACKGROUND=/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png
EOF
cat > "$ISO/etc/chimera/desktop-background.conf" <<'EOF'
# Chimera II OS Aurora desktop background.
# Replace this path to change the desktop wallpaper without rebuilding the ISO.
CHIMERA_DESKTOP_BACKGROUND=/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png
CHIMERA_LOCKSCREEN_BACKGROUND=/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png
EOF
cat > "$ISO/system/branding/chimera-background.json" <<'EOF'
{
  "schema_version": 1,
  "default": "/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png",
  "desktop": "/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png",
  "lockscreen": "/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png",
  "boot_surfaces": [
    "/boot/grub/aurora-wayland-glass.png",
    "/boot/jasper/background.png",
    "/boot/spitfire/background.png"
  ],
  "installer_surfaces": [
    "/install/installer-background.png",
    "/install/library-background.png"
  ],
  "changeable": true
}
EOF
echo "[Chimera][AURORA] Applied supplied artwork to all boot, installer and desktop surfaces."
