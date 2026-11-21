#!/usr/bin/env bash
set -Eeuo pipefail

# Compress the source material carried by a large Chimera II OS ISO without
# changing boot-critical or runtime paths. The resulting archive is an ISO
# payload and is never executed directly by firmware.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ISO_DIR="${1:?usage: compress-source-payload.sh ISO_DIR [SOURCE_ROOT] }"
SOURCE_ROOT="${2:-$SCRIPT_DIR}"
SOURCE_DIR="$ISO_DIR/source"
WORK_DIR="${CHIMERA_ISO_TMPDIR:-/tmp/chimera-iso-build}/source-payload"
ARCHIVE="$SOURCE_DIR/chimera-source.tar.zst"
MANIFEST="$SOURCE_DIR/chimera-source-manifest.json"
FORMAT="zstd"
LEVEL="${CHIMERA_SOURCE_COMPRESSION_LEVEL:-19}"

mkdir -p "$SOURCE_DIR" "$WORK_DIR"
rm -rf "$WORK_DIR/tree"
mkdir -p "$WORK_DIR/tree"

command -v tar >/dev/null || { echo "tar is required" >&2; exit 2; }
command -v zstd >/dev/null || { echo "zstd is required for compressed ISO source payloads" >&2; exit 2; }

# Never put build outputs, VCS metadata, caches, credentials, or generated
# runtime state into the source archive.
EXCLUDES=(
  --exclude=.git
  --exclude=.github/workflows/*.log
  --exclude=build
  --exclude=chimera-build
  --exclude=chimera-output
  --exclude=.cache
  --exclude=.venv
  --exclude=venv
  --exclude=node_modules
  --exclude=__pycache__
  --exclude='*.pyc'
  --exclude='*.pyo'
  --exclude='*.swp'
  --exclude='*.swo'
  --exclude='*.iso'
  --exclude='*.img'
  --exclude='*.squashfs'
  --exclude='*.vhdx'
  --exclude='*.qcow2'
  --exclude='*.log'
  --exclude='*.pem'
  --exclude='*.key'
  --exclude='*.p12'
  --exclude='*.pfx'
)

# Build a normalized source snapshot in a temporary directory so the archive
# has a stable top-level directory and never captures the build directory.
rm -rf "$WORK_DIR/tree/ChimeraIIOS"
mkdir -p "$WORK_DIR/tree/ChimeraIIOS"

tar -C "$SOURCE_ROOT" "${EXCLUDES[@]}" -cf - . | tar -C "$WORK_DIR/tree/ChimeraIIOS" -xf -

SOURCE_BYTES="$(du -sb "$WORK_DIR/tree/ChimeraIIOS" | awk '{print $1}')"
SOURCE_FILES="$(find "$WORK_DIR/tree/ChimeraIIOS" -type f | wc -l | tr -d ' ')"

rm -f "$ARCHIVE"
tar -C "$WORK_DIR/tree" -cf - ChimeraIIOS | zstd -T0 -"$LEVEL" -q -o "$ARCHIVE"

COMPRESSED_BYTES="$(stat -c%s "$ARCHIVE" 2>/dev/null || stat -f%z "$ARCHIVE")"
SHA256="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
RATIO="unknown"
if [[ "$SOURCE_BYTES" =~ ^[0-9]+$ && "$SOURCE_BYTES" -gt 0 ]]; then
  RATIO="$(awk -v a="$SOURCE_BYTES" -v b="$COMPRESSED_BYTES" 'BEGIN {printf "%.3f", b/a}')"
fi

cat > "$MANIFEST" <<EOF
{
  "schema": "CHM-ISO-SOURCE-COMPRESSED-1",
  "archive": "/source/chimera-source.tar.zst",
  "format": "tar+zstd",
  "compression": "zstd",
  "compression_level": $LEVEL,
  "source_root": "repository-worktree",
  "source_bytes": $SOURCE_BYTES,
  "compressed_bytes": $COMPRESSED_BYTES,
  "compression_ratio": "$RATIO",
  "file_count": $SOURCE_FILES,
  "sha256": "$SHA256",
  "runtime_executable": false,
  "boot_critical": false,
  "extract_command": "zstd -dc /source/chimera-source.tar.zst | tar -xpf -"
}
EOF

# A second checksum is useful for ISO verification without requiring archive
# extraction.
printf '%s  %s\n' "$SHA256" "$(basename "$ARCHIVE")" > "$ARCHIVE.sha256"

# The source bundle is the canonical source copy on the ISO. Do not leave an
# uncompressed repository mirror beside it.
rm -rf "$ISO_DIR/src"

printf 'SOURCE_ARCHIVE=%s\nSOURCE_MANIFEST=%s\nSOURCE_BYTES=%s\nCOMPRESSED_BYTES=%s\nSHA256=%s\n' \
  "$ARCHIVE" "$MANIFEST" "$SOURCE_BYTES" "$COMPRESSED_BYTES" "$SHA256"
