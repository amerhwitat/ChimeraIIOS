#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_REPO_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${CHIMERA_AURORA_ASSET:-}"

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

# Decode an embedded artwork defensively. In addition to CR/LF/BOM and other
# transport noise, older/generated assets can contain exactly one stray base64
# character. Python's b64decode reports that as "number of data characters ...
# cannot be 1 more than a multiple of 4". We only attempt recovery when the
# decoded bytes have the expected image signature; arbitrary payloads are not
# silently accepted.
decode_embedded() {
  local src="$1" dst="$2" magic="$3"
  [[ -s "$src" ]] || return 1
  mkdir -p "$(dirname "$dst")"

  if command -v python3 >/dev/null 2>&1; then
    if python3 - "$src" "$dst" "$magic" <<'PY'
import base64
import pathlib
import re
import sys

src, dst, magic = sys.argv[1], sys.argv[2], sys.argv[3]
raw = pathlib.Path(src).read_bytes().lstrip(b"\xef\xbb\xbf")
clean = re.sub(rb"[^A-Za-z0-9+/=]", b"", raw)
expected = bytes.fromhex(magic)

# First try the canonical payload. If its length is 1 (mod 4), try removing
# one suspicious base64 character from the tail. The exact failure reported by
# Python is otherwise fatal; recovery is accepted only when the image magic is
# correct and the decoded stream is non-empty.
candidates = [clean]
if len(clean) % 4 == 1:
    candidates.extend(clean[:len(clean)-1-i] + clean[len(clean)-i:] for i in range(min(16, len(clean))))

for candidate in candidates:
    candidate += b"=" * ((-len(candidate)) % 4)
    try:
        data = base64.b64decode(candidate, validate=False)
    except Exception:
        continue
    if data.startswith(expected) and len(data) > len(expected):
        pathlib.Path(dst).write_bytes(data)
        raise SystemExit(0)

raise SystemExit("invalid base64 artwork payload")
PY
    then return 0; fi
  fi

  if base64 --help 2>&1 | grep -q -- '--ignore-garbage'; then
    if base64 --ignore-garbage -d "$src" > "$dst" 2>/dev/null; then
      local got
      got="$(od -An -tx1 -N8 "$dst" 2>/dev/null | tr -d ' \n')"
      [[ "$got" == "$magic" ]] && return 0
    fi
  fi
  rm -f "$dst"
  return 1
}

normalize_to_png() {
  local src="$1" dst="$2"
  if [[ "$(file -b "$src" 2>/dev/null || true)" == *"PNG image data"* ]]; then
    cp "$src" "$dst"
    return 0
  fi
  if command -v convert >/dev/null 2>&1; then
    convert "$src" "$dst"
    return 0
  fi
  if command -v magick >/dev/null 2>&1; then
    magick "$src" "$dst"
    return 0
  fi
  return 1
}

if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  mkdir -p "$ROOT/build/branding"
  if decode_embedded "$EMBEDDED_PNG" "$ROOT/build/branding/aurora-default.png" "89504e470d0a1a0a"; then
    OUT="$ROOT/build/branding/aurora-default.png"
    echo "[Chimera][AURORA] Using embedded offline Aurora PNG artwork."
  elif decode_embedded "$EMBEDDED" "$ROOT/build/branding/aurora-default.jpg" "ffd8ff"; then
    OUT="$ROOT/build/branding/aurora-default.jpg"
    echo "[Chimera][AURORA] Using embedded offline Aurora JPEG fallback artwork."
  fi
fi

if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then
  echo "[Chimera][AURORA] External/embedded image not found or failed validation; SVG fallback remains active."
  exit 0
fi

ISO="${1:?ISO staging directory required}"
ROOTFS_DIR="${CHIMERA_ROOTFS_DIR:-$(cd "$(dirname "$ISO")/.." 2>/dev/null && pwd)/rootfs}"
mkdir -p "$ISO/boot/grub" "$ISO/boot/jasper" "$ISO/boot/spitfire" "$ISO/install" "$ISO/desktop/aurora" "$ISO/desktop/aurora/backgrounds" "$ISO/system/branding" "$ISO/usr/share/backgrounds/chimera" "$ISO/usr/share/chimera/aurora" "$ISO/etc/chimera" "$ROOTFS_DIR/usr/share/backgrounds/chimera" "$ROOTFS_DIR/usr/share/chimera/aurora" "$ROOTFS_DIR/etc/chimera"

NORMALIZED="$ROOT/build/branding/aurora-staged.png"
if ! normalize_to_png "$OUT" "$NORMALIZED"; then
  echo "[Chimera][AURORA] Cannot normalize artwork to PNG; SVG fallback remains active."
  exit 0
fi
OUT="$NORMALIZED"

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
