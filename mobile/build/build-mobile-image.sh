#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: mobile/build/build-mobile-image.sh

Usage:
  mobile/build/build-mobile-image.sh [options] [arguments]

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
PROFILE="${1:-$ROOT/mobile/device-profiles/reference-aarch64.json}"
OUT="${2:-$ROOT/mobile/images/dist}"
python3 "$ROOT/mobile/build/validate-profile.py" "$PROFILE"

# Constrain cleanup to the repository's mobile image workspace.
python3 - "$ROOT" "$OUT" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
if out.is_symlink():
    raise SystemExit("refusing symlink output directory")
resolved = out.resolve()
allowed = (root / "mobile" / "images").resolve()
if resolved == allowed or allowed not in resolved.parents:
    raise SystemExit(f"output must be a child of {allowed}: {resolved}")
if resolved == root or resolved == Path("/"):
    raise SystemExit("refusing unsafe output path")
PY
STAGE="$OUT.tmp.$$"
trap 'rm -rf -- "$STAGE"' EXIT
rm -rf -- "$STAGE"
mkdir -p "$STAGE"
cp "$PROFILE" "$STAGE/device-profile.json"
python3 - "$PROFILE" "$STAGE/mobile-image-manifest.json" <<'PY'
import json, sys
from pathlib import Path
profile = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
manifest = {
    "schema": "CHM-MOBILE-IMAGE-RESEARCH-1",
    "profile": profile["id"],
    "architecture": profile["architecture"],
    "support_status": profile["support_status"],
    "flashable": False,
    "reason": "No hardware-validated device boot bundle, vendor modules, AVB-signed images, or tested adapter is supplied."
}
Path(sys.argv[2]).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY
rm -rf -- "$OUT"
mv -- "$STAGE" "$OUT"
trap - EXIT
printf 'Chimera Mobile research layout prepared at %s\n' "$OUT"
printf '%s\n' 'NOT FLASHABLE: no device-specific signed boot bundle is present.'
printf '%s\n' 'Production images require exact device kernel/vendor modules, AVB signing, rollback metadata and hardware boot tests.'
