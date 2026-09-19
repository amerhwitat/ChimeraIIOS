#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
python3 "$ROOT/installer/chimera_installer.py" --output "$ROOT/chimera-install-plan.json" "$@"
