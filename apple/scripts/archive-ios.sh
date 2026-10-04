#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: apple/scripts/archive-ios.sh

Usage:
  apple/scripts/archive-ios.sh [options] [arguments]

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
: "${SCHEME:?Set SCHEME}"
CONFIGURATION="${CONFIGURATION:-Release}"
mkdir -p build/archive build/DerivedData
if [[ -n "${WORKSPACE:-}" ]]; then
  xcodebuild -workspace "$WORKSPACE" -scheme "$SCHEME" -configuration "$CONFIGURATION" -destination 'generic/platform=iOS' -derivedDataPath build/DerivedData -archivePath "build/archive/${SCHEME}.xcarchive" archive
elif [[ -n "${PROJECT:-}" ]]; then
  xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration "$CONFIGURATION" -destination 'generic/platform=iOS' -derivedDataPath build/DerivedData -archivePath "build/archive/${SCHEME}.xcarchive" archive
else
  echo 'Set WORKSPACE or PROJECT' >&2; exit 2
fi
