#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
if [[ "${CHIMERA_GUI:-1}" == "1" ]]; then exec python3 desktop/aurora/gui_server.py; fi
exec "$@"
