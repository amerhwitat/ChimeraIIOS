#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPRESSOR="$ROOT/tools/iso/compress-source-payload.sh"
VERIFY="$ROOT/tools/iso/verify-source-compression.sh"

bash -n "$COMPRESSOR"
bash -n "$VERIFY"

if ! command -v zstd >/dev/null 2>&1; then
  echo "SKIP: zstd is not installed"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/source-tree/ChimeraIIOS/src" "$TMP/source-tree/ChimeraIIOS/build"
printf '%s\n' 'source payload' > "$TMP/source-tree/ChimeraIIOS/src/example.txt"
printf '%s\n' 'generated build output' > "$TMP/source-tree/ChimeraIIOS/build/generated.txt"

bash "$COMPRESSOR" "$TMP/iso" "$TMP/source-tree"
test -s "$TMP/iso/source/chimera-source.tar.zst"
test -s "$TMP/iso/source/chimera-source-manifest.json"
test -s "$TMP/iso/source/chimera-source.tar.zst.sha256"
bash "$VERIFY" "$TMP/iso"

# Build artifacts must be excluded from the source archive.
! zstd -q -dc "$TMP/iso/source/chimera-source.tar.zst" | tar -tf - | grep -q '/build/generated.txt$'
zstd -q -dc "$TMP/iso/source/chimera-source.tar.zst" | tar -tf - | grep -q 'ChimeraIIOS/src/example.txt'

echo 'PASS: compressed source payload'
