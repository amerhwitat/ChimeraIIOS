#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CTL="$ROOT/tools/runtime/chimera-nbit-mode.py"
NEURAL="$ROOT/tools/runtime/chimera-neural-dim.py"
get(){ "$CTL" get 2>/dev/null || printf '{"width":8192,"style":"RISC","execution":"NativeWide"}'; }
render(){ python3 - "$1" "$2" <<'PY'
import json,sys
d=json.loads(sys.argv[1]); n=json.loads(sys.argv[2])
print("AURORA | CHIMERA II | ISA N{} {} {} | NEURAL {}D {} | LIVE / NO REBOOT".format(d["width"],d["style"],d["execution"],n["dimensions"],n["representation"]))
PY
}
while :; do render "$(get)" "$("$NEURAL" get 2>/dev/null || printf '{"dimensions":1024,"representation":"HyperDimensional","learning":"AdaptiveTensor"}')"; sleep 1; done
