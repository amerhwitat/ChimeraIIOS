#!/usr/bin/env bash
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
