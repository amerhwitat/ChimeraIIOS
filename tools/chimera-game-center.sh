#!/bin/sh
set -eu
CFG=/usr/share/chimera/aurora/config/game-center.json
[ -r "$CFG" ] || CFG=./config/aurora/game-center.json
echo "Aurora Desktop — Game Center"
echo "Console and computer emulator families:"
if command -v python3 >/dev/null 2>&1; then
 python3 - "$CFG" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
last=None
for x in d["systems"]:
 if x["family"]!=last:
  last=x["family"]; print("\n["+last+"]")
 print("  %-20s %-30s %s"%(x["id"],x["hardware"],x["backend"]))
PY
else
 echo "Python 3 is required to enumerate the Game Center registry."
fi
echo
echo "Use Aurora Game Center to scan/import user-owned or legally redistributable game content."

G3D=/usr/share/chimera/aurora/config/free-3d-games.json
[ -r "$G3D" ] || G3D=./config/aurora/free-3d-games.json
if [ -r "$G3D" ] && command -v python3 >/dev/null 2>&1; then
 echo
 echo "[Free 3D Games]"
 python3 - "$G3D" <<'PY3'
import json,sys
for g in json.load(open(sys.argv[1],encoding="utf-8"))["games"]:
 print("  %-18s %-24s %s" % (g["id"],g["title"],g["genre"]))
PY3
fi
