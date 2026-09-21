#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT/tools/build/build-hosted.sh"
if [[ -x "$ROOT/tools/build/build-baremetal.sh" ]]; then "$ROOT/tools/build/build-baremetal.sh"; fi
if [[ -x "$ROOT/tools/build/build-mobile.sh" ]]; then "$ROOT/tools/build/build-mobile.sh"; fi
printf 'Chimera II OS build matrix orchestration finished.\n'
