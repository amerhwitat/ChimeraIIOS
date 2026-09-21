#!/usr/bin/env bash

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
