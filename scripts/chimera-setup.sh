#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/tools/build/orchestrator.py" all "$@"
python3 "$ROOT/tools/build/orchestrator.py" install "$@"
