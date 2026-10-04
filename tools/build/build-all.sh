#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build/build-all.sh

Usage:
  tools/build/build-all.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT/tools/build/build-hosted.sh"
if [[ -x "$ROOT/tools/build/build-baremetal.sh" ]]; then "$ROOT/tools/build/build-baremetal.sh"; fi
if [[ -x "$ROOT/tools/build/build-mobile.sh" ]]; then "$ROOT/tools/build/build-mobile.sh"; fi
printf 'Chimera II OS build matrix orchestration finished.\n'
