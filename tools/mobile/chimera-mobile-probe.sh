#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/mobile/chimera-mobile-probe.sh

Usage:
  tools/mobile/chimera-mobile-probe.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="$SCRIPT_DIR/chimera-device-port-scan.py"
OUT="${1:-}"
command -v python3 >/dev/null 2>&1 || { echo '{"error":"python3 is required"}' >&2; exit 2; }
[[ -f "$SCANNER" ]] || { echo '{"error":"universal port scanner is missing"}' >&2; exit 2; }
if [[ -n "$OUT" ]]; then
  python3 "$SCANNER" --json | tee "$OUT"
else
  exec python3 "$SCANNER" --json
fi
