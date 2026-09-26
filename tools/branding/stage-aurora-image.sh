#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${CHIMERA_AURORA_ASSET:-}"

# Search order deliberately keeps the user-provided artwork as the canonical default.
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

# Decode a repository-embedded artwork defensively. Git/Windows transport can
# introduce CR/LF/BOM/other harmless characters into a text-encoded asset; GNU
# base64 otherwise reports "invalid input" and aborts the staging step. We
# sanitize only the base64 alphabet, decode, and then verify the PNG signature.
decode_embedded_png() {
  local src="$1" dst="$2"
  [[ -s "$src" ]] || return 1
  mkdir -p "$(dirname "$dst")"

  if command -v python3 >/dev/null 2>&1; then
    if python3 - "$src" "$dst" <<'PY'
import base64
import pathlib
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
raw = pathlib.Path(src).read_bytes()
# Remove UTF-8 BOM and every non-base64 transport character.
raw = raw.lstrip(b"\xef\xbb\xbf")
clean = re.sub(rb"[^A-Za-z0-9+/=]", b"", raw)
# Normalize missing terminal padding without accepting an impossible length.
if len(clean) % 4 == 1:
    raise SystemExit("invalid base64 payload length")
clean += b"=" * ((-len(clean)) % 4)
data = base64.b64decode(clean, validate=False)
if data[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("decoded payload is not a PNG")
pathlib.Path(dst).write_bytes(data)
PY
    then
      return 0
    fi
  fi

  # GNU coreutils fallback. --ignore-garbage handles CR/LF/BOM/transport noise.
  if base64 --help 2>&1 | grep -q -- '--ignore-garbage'; then
    if base64 --ignore-garbage -d "$src" > "$dst" 2>/dev/null; then
      if [[ "$(od -An -tx1 -N8 "$dst" 2>/dev/null | tr -d ' \n')" == "89504e470d0a1a0a" ]]; then
        return 0
      fi
    fi
  fi

  rm -f "$dst"
  return 1
}

if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  mkdir -p "$ROOT/build/branding"
  if command -v base64 >/dev/null 2>&1 && decode_embedded_png "$EMBEDDED_PNG" "$ROOT/build/branding/aurora-default.png"; then
    OUT="$ROOT/build/branding/aurora-default.png"
    echo "[Chimera][AURORA] Using embedded offline Aurora PNG artwork."
  elif command -v base64 >/dev/null 2>&1 && [[ -s "$EMBEDDED" ]]; then
    # JPEG fallback remains supported, but validate the decode before using it.
    if command -v python3 >/dev/null 2>&1 && python3 - "$EMBEDDED" "$ROOT/build/branding/aurora-default.jpg" <<'PY'
import base64, pathlib, re, sys
src, dst = sys.argv[1], sys.argv[2]
raw = pathlib.Path(src).read_bytes().lstrip(b"\xef\xbb\xbf")
clean = re.sub(rb"[^A-Za-z0-9+/=]", b"", raw)
clean += b"=" * ((-len(clean)) % 4)
data = base64.b64decode(clean, validate=False)
if not data.startswith(b"\xff\xd8\xff"):
    raise SystemExit("decoded payload is not a JPEG")
pathlib.Path(dst).write_bytes(data)
PY
    then
      OUT="$ROOT/build/branding/aurora-default.jpg"
      echo "[Chimera][AURORA] Using embedded offline Aurora JPEG fallback artwork."
    else
      rm -f "$ROOT/build/branding/aurora-default.jpg"
    fi
  fi
fi

if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  echo "[Chimera][AURORA] External/embedded image not found or failed validation; SVG fallback remains active."
  exit 0
fi

ISO="${1:?ISO staging directory required}"
ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:-$(cd "$(dirname "$ISO")/.." 2>/dev/null && pwd)/rootfs}"
mkdir -p "$ISO/boot/grub" "$ISO/boot/jasper" "$ISO/boot/spitfire" "$ISO/install" "$ISO/desktop/aurora" "$ISO/desktop/aurora/backgrounds" "$ISO/system/branding" "$ISO/usr/share/backgrounds/chimera" "$ISO/usr/share/chimera/aurora" "$ISO/etc/chimera" "$ROOTFS_DIR/usr/share/backgrounds/chimera" "$ROOTFS_DIR/usr/share/chimera/aurora" "$ROOTFS_DIR/etc/chimera"
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

cp "$OUT" "$ROOTFS_DIR/usr/share/backgrounds/chimera/Aurora-Wayland-Glass-Desktop.png"
cp "$OUT" "$ROOTFS_DIR/usr/share/chimera/aurora/aurora-wayland-glass.png"

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
