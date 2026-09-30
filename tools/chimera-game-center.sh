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
