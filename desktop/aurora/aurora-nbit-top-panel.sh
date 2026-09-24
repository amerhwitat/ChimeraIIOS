#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CTL="$ROOT/tools/runtime/chimera-nbit-mode.py"
get(){ "$CTL" get 2>/dev/null || printf '{"width":8192,"style":"RISC","execution":"NativeWide"}'; }
render(){ python3 - "$1" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
print("AURORA | CHIMERA II ISA | N{} | {} | {} | UP/DOWN change width | LIVE / NO REBOOT".format(d["width"],d["style"],d["execution"]))
PY
}
while :; do render "$(get)"; sleep 1; done
