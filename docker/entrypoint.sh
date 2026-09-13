#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 0 ]]; then exec "$@"; fi
if [[ -f /app/CMakeLists.txt ]]; then cmake -S /app -B /tmp/chimera-build -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/chimera-build -j"$(nproc)"; printf '%s\n' 'ChimeraIIOS container build completed.' 'Use an explicit command to run a selected emulator/tool.'; exec bash; fi
exec bash
