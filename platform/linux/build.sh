#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
printf 'Chimera II Linux build environment\n'
printf 'Repository: %s\n' "$ROOT"
command -v gcc >/dev/null || { echo 'gcc is required'; exit 1; }
command -v python3 >/dev/null || { echo 'python3 is required'; exit 1; }
python3 "$ROOT/appcenter/cli/chimera-appctl.py" list
