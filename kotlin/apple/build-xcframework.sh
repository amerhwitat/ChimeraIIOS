#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/build/xcframework"
mkdir -p "$OUT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Kotlin/Native Apple framework compilation requires macOS." >&2
  exit 2
fi

if [[ -z "${KMP_XCFRAMEWORK_TASK:-}" ]]; then
  echo "Set KMP_XCFRAMEWORK_TASK to the repository-specific Gradle XCFramework task." >&2
  echo "Typical Kotlin Multiplatform task: assembleTogetherReleaseXCFramework" >&2
  exit 2
fi

if [[ -x "$ROOT/gradlew" ]]; then
  "$ROOT/gradlew" "$KMP_XCFRAMEWORK_TASK"
else
  echo "No Gradle wrapper found at $ROOT; run the task from the KMP module that owns the shared framework." >&2
  exit 2
fi
