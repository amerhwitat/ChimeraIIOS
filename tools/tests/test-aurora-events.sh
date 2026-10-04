#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/tests/test-aurora-events.sh

Usage:
  tools/tests/test-aurora-events.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVENT="$ROOT/desktop/aurora/aurora-event-sound.sh"
[[ -f "$EVENT" ]] || { echo "missing: $EVENT" >&2; exit 1; }
[[ "$(bash "$EVENT" --known menu_select)" == "menu-select.wav" ]]
[[ "$(bash "$EVENT" --known unknown-event)" == "" ]]
CHIMERA_SOUND_ENABLED=0 bash "$EVENT" menu_select >/dev/null 2>&1
printf 'PASS: Aurora event sound contract\n'
