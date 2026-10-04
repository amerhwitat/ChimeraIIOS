#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/emulators/verify-sakhr-roms.sh

Usage:
  aurora/emulators/verify-sakhr-roms.sh [options] [arguments]

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
ROMDIR="${SAKHR_ROMDIR:-$ROOT/../BizX/emulators/sakhr/roms/binary}"
[[ -d "$ROMDIR" ]] || ROMDIR="$ROOT/emulators/sakhr/roms/binary"
fail=0
verify(){ local f="$1" sha="$2" size="$3"; local p="$ROMDIR/$f"; if [[ ! -f "$p" ]]; then echo "MISSING $f"; fail=1; return; fi; [[ "$(wc -c < "$p" | tr -d ' ')" == "$size" ]] || { echo "BAD-SIZE $f"; fail=1; return; }; [[ "$(sha1sum "$p" | awk '{print $1}')" == "$sha" ]] || { echo "BAD-SHA1 $f"; fail=1; return; }; echo "OK $f"; }
verify ax170arab.rom 0287b2ec897b9196788cd9f10c99e1487d7adbbb 32768
verify ax170bios.rom 5e094fca95ab8e91873ee372a3f1239b9a48a48d 32768
verify IC125.BIN 0340707c5de2310dcf5e569b7db4c6a6a5590cb7 131072
verify IC127.BIN 620a209bdfdb65a22380031fce654bd1df61def2 1048576
if (( fail )); then echo "Sakhr ROM verification: FAILED"; exit 2; fi
echo "Sakhr ROM verification: PASS"
