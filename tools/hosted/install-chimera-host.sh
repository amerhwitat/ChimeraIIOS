#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${CHIMERA_HOST_PREFIX:-$HOME/.local/chimera}"
mkdir -p "$PREFIX/bin"
install -m 0755 "$ROOT/tools/hosted/chimera-host-run.sh" "$PREFIX/bin/chimera-host-run"
install -m 0755 "$ROOT/tools/hosted/chimera-host-detect.sh" "$PREFIX/bin/chimera-host-detect"
echo "Installed Chimera II hosted launchers in $PREFIX/bin"
