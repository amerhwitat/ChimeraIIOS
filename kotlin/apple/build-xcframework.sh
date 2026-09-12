#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/build/xcframework"
mkdir -p "$OUT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Kotlin/Native Apple framework compilation requires macOS." >&2
  exit 2
fi

if [[ -x "$ROOT/gradlew" ]]; then
  "$ROOT/gradlew" :kotlin:apple:assembleTogetherReleaseXCFramework
else
  echo "No root Gradle wrapper for the shared module; integrate this contract into the repository's KMP Gradle project." >&2
  exit 2
fi
