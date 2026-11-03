#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$1"
if [[ -z "$OUT" ]]; then OUT="$ROOT/build/polyglot-apps"; fi
python3 "$ROOT/tools/polyglot_apps.py" --root "$ROOT" --output "$OUT" --platform linux
