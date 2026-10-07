#!/usr/bin/env bash
set -euo pipefail
MANIFEST="$CHIMERA_PLAYSTATION_MANIFEST"
ROOT="$CHIMERA_EMULATOR_ROOT"
[[ -n "$MANIFEST" ]] || MANIFEST="/usr/share/chimera/web/playstation_emulators.json"
[[ -n "$ROOT" ]] || ROOT="$HOME/.local/share/chimera/emulators"
if [[ ! -r "$MANIFEST" ]]; then
  SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
  MANIFEST="$SCRIPT_DIR/../../web/playstation_emulators.json"
fi
[[ -r "$MANIFEST" ]] || { echo "ERROR: manifest not found: $MANIFEST" >&2; exit 2; }

python3 - "$MANIFEST" "$ROOT" "$@" <<'PY'
import json, os, shutil, sys
manifest, root = sys.argv[1:3]
args = sys.argv[3:]
data = json.load(open(manifest, encoding="utf-8"))
items = [e for g in data["generations"] for e in g["emulators"]]

def find_exec(item):
    for name in item.get("executable_candidates", []):
        p = shutil.which(name)
        if p: return p
        for base in (root, os.path.expanduser("~/.local/bin"), "/usr/local/bin", "/opt/chimera/emulators"):
            q = os.path.join(base, name)
            if os.path.isfile(q) and os.access(q, os.X_OK): return q
    return None

if not args or args[0] == "help":
    print("Use list, detect <id>, or run <id> <media>. Games and firmware are user supplied.")
    raise SystemExit(0)

if args[0] == "list":
    for item in items:
        exe = find_exec(item)
        needs = []
        if item.get("bios_required"): needs.append("BIOS")
        if item.get("firmware_required"): needs.append("FIRMWARE")
        print(f'{item["id"]:16} {item["title"]:28} {"INSTALLED" if exe else "NOT INSTALLED":14} {item["status"]} {" ".join(needs)}')
    raise SystemExit(0)

if len(args) < 2:
    raise SystemExit(2)
item = next((x for x in items if x["id"] == args[1]), None)
if not item:
    print("Unknown emulator:", args[1], file=sys.stderr); raise SystemExit(2)

exe = find_exec(item)
if args[0] == "detect":
    print(json.dumps({"id":item["id"],"title":item["title"],"installed":bool(exe),"executable":exe,"status":item["status"],"requirements":item.get("requirements",[])}, indent=2))
    raise SystemExit(0)

if args[0] == "run":
    if not exe: raise SystemExit("ERROR: emulator is not installed")
    if len(args) < 3: raise SystemExit("ERROR: media/game path is required")
    media = os.path.abspath(os.path.expanduser(args[2]))
    if not os.path.exists(media): raise SystemExit("ERROR: media not found: "+media)
    os.execv(exe, [exe, media])
raise SystemExit(2)
PY
