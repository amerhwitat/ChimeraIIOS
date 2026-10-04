#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/emulators/bin/launch-sakhr-ax230.sh

Usage:
  aurora/emulators/bin/launch-sakhr-ax230.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="${CHIMERA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
ROMDIR="${CHIMERA_SAKHR_ROMDIR:-$ROOT/../BizX/emulators/sakhr/roms/binary}"
[[ -d "$ROMDIR" ]] || ROMDIR="$ROOT/emulators/sakhr/roms/binary"
[[ -f "$ROMDIR/IC125.BIN" && -f "$ROMDIR/IC127.BIN" ]] || { echo "Sakhr AX-230 ROMs not installed. Run BizX/emulators/sakhr/roms/fetch_sakhr_roms.sh first." >&2; exit 2; }
BRIDGE="$ROOT/aurora/emulators/bin/aurora-emulator-window.sh"
[[ -x "$BRIDGE" ]] || { echo "Aurora emulator window bridge missing: $BRIDGE" >&2; exit 127; }
if command -v openmsx >/dev/null 2>&1; then
  exec "$BRIDGE" sakhr-ax230 "Sakhr AX-230" openmsx -machine Al_Alamiah_AX230 "$@"
fi
if command -v mame >/dev/null 2>&1; then
  exec "$BRIDGE" sakhr-ax230 "Sakhr AX-230" mame ax230 "$@"
fi
echo "No OpenMSX or MAME runtime found for Sakhr AX-230." >&2
exit 127
