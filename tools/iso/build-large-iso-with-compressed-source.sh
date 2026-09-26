#!/usr/bin/env bash
set -Eeuo pipefail

# Compatibility wrapper around build-chimera-iso.sh. It injects the source
# compression stage immediately before SquashFS creation, so source material
# never becomes a second uncompressed copy of the ISO payload.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE="$REPO_ROOT/build-chimera-iso.sh"
COMPRESSOR="$REPO_ROOT/tools/iso/compress-source-payload.sh"
TMP_ROOT="${CHIMERA_ISO_TMPDIR:-/tmp/chimera-iso-build}"
PATCHED="$TMP_ROOT/build-chimera-iso-source-compressed.$$"

[[ -f "$BASE" ]] || { echo "Missing base builder: $BASE" >&2; exit 2; }
[[ -f "$COMPRESSOR" ]] || { echo "Missing source compressor: $COMPRESSOR" >&2; exit 2; }
mkdir -p "$TMP_ROOT"
trap 'rm -f "$PATCHED"' EXIT

# Insert exactly once before the existing SquashFS stage. The base script is
# deliberately retained so storage detection, Docker/WSL handling, boot,
# installer, resumable checkpoints, ISO mastering and verification remain the
# authoritative implementation.
awk -v compressor="$COMPRESSOR" '
BEGIN { inserted=0 }
{
  if (!inserted && $0 ~ /if \[ \! build_state_done "\$completed_stage" squashfs \]/) {
    print "    if [[ \"${CHIMERA_COMPRESS_SOURCE:-1}\" = \"1\" ]]; then"
    print "        CURRENT_STAGE=source-compression"
    print "        bash \"" compressor "\" \"$ISO_DIR\" \"$SCRIPT_DIR\""
    print "        CURRENT_STAGE=\"\""
    print "        build_state_mark source-compression"
    print "    fi"
    inserted=1
  }
  print
}
END {
  if (!inserted) {
    print "ERROR: could not locate SquashFS stage in build-chimera-iso.sh" > "/dev/stderr"
    exit 3
  }
}' "$BASE" > "$PATCHED"

chmod +x "$PATCHED"
exec bash "$PATCHED" "$@"
