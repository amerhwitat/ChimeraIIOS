#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT/tools/build/build-hosted.sh"
if [[ -x "$ROOT/tools/build/build-baremetal.sh" ]]; then "$ROOT/tools/build/build-baremetal.sh"; fi
if [[ -x "$ROOT/tools/build/build-mobile.sh" ]]; then "$ROOT/tools/build/build-mobile.sh"; fi
printf 'Chimera II OS build matrix orchestration finished.\n'
