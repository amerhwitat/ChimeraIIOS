#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
ID="${1:?retro emulator id required}"
shift || true
BRIDGE="$ROOT/aurora/emulators/bin/aurora-emulator-window.sh"
[[ -x "$BRIDGE" ]] || { echo "Aurora emulator window bridge missing: $BRIDGE" >&2; exit 127; }

case "$ID" in
  sakhr-ax170) exec "$ROOT/aurora/emulators/bin/launch-sakhr-ax170.sh" "$@" ;;
  sakhr-ax230) exec "$ROOT/aurora/emulators/bin/launch-sakhr-ax230.sh" "$@" ;;
  retro-spectrum)
    if command -v fuse >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Sinclair ZX Spectrum" fuse "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Sinclair ZX Spectrum" mame spectrum "$@"; fi
    ;;
  retro-atari-st)
    if command -v hatari >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Atari ST" hatari "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Atari ST" mame st "$@"; fi
    ;;
  retro-amiga)
    if command -v fs-uae >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Amiga" fs-uae "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Amiga" mame amiga "$@"; fi
    ;;
  retro-commodore)
    if command -v x64sc >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Commodore" x64sc "$@"; fi
    if command -v vice >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Commodore" vice "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Commodore" mame c64 "$@"; fi
    ;;
  retro-apple)
    if command -v Mini\ vMac >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Apple Macintosh" Mini\ vMac "$@"; fi
    if command -v minivmac >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Apple Macintosh" minivmac "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Apple" mame macplus "$@"; fi
    ;;
  retro-acorn)
    if command -v rpcemu >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Acorn BBC/Archimedes" rpcemu "$@"; fi
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Acorn" mame bbcb "$@"; fi
    ;;
  retro-amstrad)
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Amstrad CPC" mame cpc464 "$@"; fi
    ;;
  retro-pc)
    if command -v dosbox-staging >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "DOS / PC" dosbox-staging "$@"; fi
    if command -v dosbox >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "DOS / PC" dosbox "$@"; fi
    if command -v qemu-system-i386 >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "DOS / PC" qemu-system-i386 -display gtk "$@"; fi
    ;;
  retro-arcade)
    if command -v mame >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "Arcade / Console Center" mame "$@"; fi
    if command -v retroarch >/dev/null 2>&1; then exec "$BRIDGE" "$ID" "RetroArch" retroarch "$@"; fi
    ;;
  *) echo "Unknown Aurora retro emulator id: $ID" >&2; exit 64 ;;
esac

echo "No graphical emulator backend installed for $ID." >&2
exit 127
