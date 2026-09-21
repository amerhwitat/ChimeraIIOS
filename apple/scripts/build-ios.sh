#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
: "${SCHEME:?Set SCHEME to an Xcode scheme}"
PROJECT_OR_WORKSPACE="${WORKSPACE:-${PROJECT:-}}"
: "${PROJECT_OR_WORKSPACE:?Set WORKSPACE or PROJECT}"
CONFIGURATION="${CONFIGURATION:-Release}"
mkdir -p build/DerivedData
ARGS=(-scheme "$SCHEME" -configuration "$CONFIGURATION" -destination 'generic/platform=iOS' -derivedDataPath build/DerivedData build)
if [[ "$PROJECT_OR_WORKSPACE" == *.xcworkspace ]]; then ARGS=(-workspace "$PROJECT_OR_WORKSPACE" "${ARGS[@]}"); else ARGS=(-project "$PROJECT_OR_WORKSPACE" "${ARGS[@]}"); fi
xcodebuild "${ARGS[@]}"
