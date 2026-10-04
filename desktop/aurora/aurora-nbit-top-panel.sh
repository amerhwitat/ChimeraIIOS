#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: desktop/aurora/aurora-nbit-top-panel.sh

Usage:
  desktop/aurora/aurora-nbit-top-panel.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
