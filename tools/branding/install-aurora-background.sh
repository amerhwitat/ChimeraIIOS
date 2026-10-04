#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/branding/install-aurora-background.sh

Usage:
  tools/branding/install-aurora-background.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
