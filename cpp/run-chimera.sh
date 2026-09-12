#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for exe in "$ROOT/build/gcc/chimera_server" "$ROOT/build/Release/chimera_server" "$ROOT/build/Debug/chimera_server"; do
  if [[ -x "$exe" ]]; then
    echo "[CHIMERA][RUN] $exe"
    exec "$exe" "$@"
  fi
done
echo "[CHIMERA][RUN] No native server executable found. Build first." >&2
exit 2
