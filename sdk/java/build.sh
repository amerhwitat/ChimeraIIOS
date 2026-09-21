#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname "$0")" && pwd)"
OUT="$ROOT/build/classes"
rm -rf "$OUT" "$ROOT/chimera-sdk.jar"
mkdir -p "$OUT"
javac -d "$OUT" "$ROOT"/src/org/chimera/sdk/*.java
jar --create --file "$ROOT/chimera-sdk.jar" -C "$OUT" .
