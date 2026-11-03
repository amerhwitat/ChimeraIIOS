#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# -gt 0 ]]; then OUT="$1"; else OUT="$ROOT/build/polyglot-apps"; fi
python3 "$ROOT/tools/polyglot_apps.py" --root "$ROOT" --output "$OUT" --platform linux
