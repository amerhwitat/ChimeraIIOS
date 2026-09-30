#!/usr/bin/env bash
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
