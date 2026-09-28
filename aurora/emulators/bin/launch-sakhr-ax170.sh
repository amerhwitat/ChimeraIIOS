#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
ROMDIR="$ROOT/../BizX/emulators/sakhr/roms/binary"
[[ -d "$ROMDIR" ]] || ROMDIR="$ROOT/emulators/sakhr/roms/binary"
[[ -f "$ROMDIR/ax170arab.rom" && -f "$ROMDIR/ax170bios.rom" ]] || { echo "Sakhr AX-170 ROMs not installed. Run BizX/emulators/sakhr/roms/fetch_sakhr_roms.sh first."; exit 2; }
if command -v openmsx >/dev/null 2>&1; then
  exec openmsx -machine Al_Alamiah_AX170 "$@"
fi
if command -v mame >/dev/null 2>&1; then
  exec mame ax170 "$@"
fi
echo "No OpenMSX or MAME runtime found for Sakhr AX-170." >&2
exit 127
