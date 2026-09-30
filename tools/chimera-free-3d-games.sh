#!/bin/sh
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
