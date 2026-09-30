#!/bin/sh
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
