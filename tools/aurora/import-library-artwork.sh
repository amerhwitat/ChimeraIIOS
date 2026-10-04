#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/aurora/import-library-artwork.sh

Usage:
  tools/aurora/import-library-artwork.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB="${1:-${CHIMERA_AURORA_LIBRARY_DIR:-}}"
DEST="$ROOT/desktop/aurora/assets/library"
if [[ -z "$LIB" || ! -d "$LIB" ]]; then echo "Usage: $0 /path/to/materialized/Aurora-Library" >&2; exit 2; fi
mkdir -p "$DEST"
for f in \
  "Aurora Wayland Desktop - boot background.jpg" \
  "Aurora Wayland Desktop Showcase.png" \
  "Aurora Wayland Glass Desktop.png" \
  "Aurora-Wayland-Glass-Desktop.png(1).jpg"; do
  [[ -f "$LIB/$f" ]] && cp -f "$LIB/$f" "$DEST/$f"
done
printf '[INFO] Imported Aurora Library artwork into %s\n' "$DEST"
