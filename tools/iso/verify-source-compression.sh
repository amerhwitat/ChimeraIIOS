#!/usr/bin/env bash
set -Eeuo pipefail

ISO_DIR="${1:?usage: verify-source-compression.sh ISO_DIR}"
ARCHIVE="$ISO_DIR/source/chimera-source.tar.zst"
MANIFEST="$ISO_DIR/source/chimera-source-manifest.json"
CHECKSUM="$ARCHIVE.sha256"

[[ -s "$ARCHIVE" ]] || { echo "missing compressed source archive: $ARCHIVE" >&2; exit 1; }
[[ -s "$MANIFEST" ]] || { echo "missing source manifest: $MANIFEST" >&2; exit 1; }
[[ -s "$CHECKSUM" ]] || { echo "missing source checksum: $CHECKSUM" >&2; exit 1; }
command -v zstd >/dev/null || { echo "zstd is required" >&2; exit 2; }
command -v tar >/dev/null || { echo "tar is required" >&2; exit 2; }

(
  cd "$(dirname "$ARCHIVE")"
  sha256sum -c "$(basename "$CHECKSUM")"
)

# Verify that the compressed stream is readable and contains the expected
# normalized repository root without extracting it into the ISO staging tree.
zstd -q -dc "$ARCHIVE" | tar -tf - >/tmp/chimera-source-list.$$ 
trap 'rm -f /tmp/chimera-source-list.$$' EXIT

grep -q '^ChimeraIIOS/$' /tmp/chimera-source-list.$$ || {
  echo "source archive does not contain the normalized ChimeraIIOS root" >&2
  exit 1
}

echo "Compressed ISO source payload verified: $ARCHIVE"
