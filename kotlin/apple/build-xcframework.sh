#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: kotlin/apple/build-xcframework.sh

Usage:
  kotlin/apple/build-xcframework.sh [options] [arguments]

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
