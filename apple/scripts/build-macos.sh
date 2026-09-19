#!/usr/bin/env bash
set -euo pipefail
: "${SCHEME:?Set SCHEME}"
CONFIGURATION="${CONFIGURATION:-Release}"
mkdir -p build/DerivedData
if [[ -n "${WORKSPACE:-}" ]]; then
  xcodebuild -workspace "$WORKSPACE" -scheme "$SCHEME" -configuration "$CONFIGURATION" -destination 'generic/platform=macOS' -derivedDataPath build/DerivedData build
elif [[ -n "${PROJECT:-}" ]]; then
  xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration "$CONFIGURATION" -destination 'generic/platform=macOS' -derivedDataPath build/DerivedData build
else
  echo 'Set WORKSPACE or PROJECT' >&2; exit 2
fi
