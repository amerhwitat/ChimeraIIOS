#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_B64="${CHIMERA_AURORA_BACKGROUND_B64:-$ROOT/boot/visual/aurora-wayland-glass.jpg.b64}"
TARGET_ROOT="${CHIMERA_TARGET_ROOT:-/}"
TARGET="${TARGET_ROOT%/}/usr/share/chimera/aurora/ChimeraIIOS-Aurora-Wayland-Glass.jpg"
BOOT_TARGET="${TARGET_ROOT%/}/boot/visual/aurora-wayland-glass.jpg"
mkdir -p "$(dirname "$TARGET")" "$(dirname "$BOOT_TARGET")"
[[ -s "$SOURCE_B64" ]] || { echo "Aurora background source missing: $SOURCE_B64" >&2; exit 2; }
base64 -d "$SOURCE_B64" > "$TARGET"
cp -f "$TARGET" "$BOOT_TARGET"
chmod 0644 "$TARGET" "$BOOT_TARGET"
sha256sum "$TARGET" | tee "${TARGET}.sha256"
printf 'Aurora background installed: %s\n' "$TARGET"
printf 'Boot background installed: %s\n' "$BOOT_TARGET"
