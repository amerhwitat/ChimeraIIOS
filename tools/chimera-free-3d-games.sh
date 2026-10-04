#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-free-3d-games.sh

Usage:
  tools/chimera-free-3d-games.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
CFG=/usr/share/chimera/aurora/config/free-3d-games.json
[ -r "$CFG" ] || CFG=./config/aurora/free-3d-games.json
ROOT=${CHIMERA_3D_GAME_ROOT:-/opt/chimera/games/3d}
mkdir -p "$ROOT"
echo "Aurora Desktop — Free 3D Games"
echo "Catalog: $CFG"
echo "Install root: $ROOT"
python3 - "$CFG" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
for g in d["games"]:
    print("%-18s %-24s %-22s %s" % (g["id"],g["title"],g["genre"],g["status"]))
PY
echo
echo "The catalog contains source/build metadata; it does not silently download unverified web binaries."
echo "Use CHIMERA_3D_GAME_ID=<id> with a future installer/build integration after license verification."
