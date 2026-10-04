#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/emulators/aurora-emulators-panel.sh

Usage:
  aurora/emulators/aurora-emulators-panel.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="${CHIMERA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
REG="$ROOT/aurora/emulators/emulator-registry.json"
if command -v python3 >/dev/null 2>&1; then
  python3 - "$REG" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p,encoding='utf-8'))
print('Aurora Emulators')
print('=================')
for e in data.get('entries',[]):
    print(f"{e['name']} | {e['system']} | {e['architecture']} | {e['status']}")
    for r in e.get('roms',[]): print(f"  - {r['name']}: {r['file']} [{r['sha1']}] ({r['size']} bytes)")
PY
else
  cat "$REG"
fi
