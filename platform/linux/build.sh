#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
printf 'Chimera II Linux build environment\n'
printf 'Repository: %s\n' "$ROOT"
command -v gcc >/dev/null || { echo 'gcc is required'; exit 1; }
command -v python3 >/dev/null || { echo 'python3 is required'; exit 1; }
python3 "$ROOT/appcenter/cli/chimera-appctl.py" list
