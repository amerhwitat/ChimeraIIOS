#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/chimera-playstation-center.sh

Usage:
  tools/chimera-playstation-center.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
ROOT=/var/lib/chimera/emulation/playstation
mkdir -p "$ROOT"/PSX "$ROOT"/PS2 "$ROOT"/PS3 "$ROOT"/PS4 "$ROOT"/PS5
echo "Chimera II PlayStation Center"
echo "PSX: user-owned dumps / OpenBIOS where supported"
echo "PS2: PCSX2 + user-owned BIOS"
echo "PS3: RPCS3 + user-supplied firmware"
echo "PS4: shadPS4-compatible user-supplied system software"
echo "PS5: experimental open-source targets + user-supplied system software"
echo "Commercial Final Fantasy ROMs/ISOs are not bundled."
echo "Import legally-owned dumps into $ROOT"
