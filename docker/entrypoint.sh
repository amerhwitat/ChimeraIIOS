#!/usr/bin/env bash
set -euo pipefail
if [[ "${CHIMERA_GUI:-1}" == "1" ]]; then exec python3 /app/desktop/aurora/gui_server.py; fi
exec "$@"
