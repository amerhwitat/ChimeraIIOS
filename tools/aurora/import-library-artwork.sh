#!/usr/bin/env bash
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
