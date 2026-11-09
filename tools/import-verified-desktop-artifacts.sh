#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="${1:-}"
DEST="${2:-$ROOT/.cache/verified-desktop-compat-tools}"
if [[ -z "$ARCHIVE" || ! -s "$ARCHIVE" ]]; then
  echo "Usage: $0 ARTIFACT.zip [destination]" >&2
  exit 64
fi
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 69; }
command -v sha256sum >/dev/null 2>&1 || { echo "sha256sum is required" >&2; exit 69; }

TMP="$(mktemp -d)"
STAGED="$DEST.importing.$$"
cleanup() { rm -rf "$TMP" "$STAGED"; }
trap cleanup EXIT

python3 - "$ARCHIVE" "$TMP" <<'PY'
from pathlib import Path
import sys
import zipfile

archive = Path(sys.argv[1])
root = Path(sys.argv[2]).resolve()
with zipfile.ZipFile(archive) as zf:
    names = zf.namelist()
    if "SHA256SUMS" not in names or not any(n.startswith("bin/") for n in names):
        raise SystemExit("artifact is missing SHA256SUMS or bin/ payload")
    for info in zf.infolist():
        target = (root / info.filename).resolve()
        if target != root and root not in target.parents:
            raise SystemExit(f"unsafe artifact member path: {info.filename}")
    zf.extractall(root)
PY

(
  cd "$TMP"
  sha256sum -c SHA256SUMS
)
test -d "$TMP/bin"
test -d "$TMP/share"
mkdir -p "$(dirname "$DEST")"
rm -rf "$STAGED"
mkdir -p "$STAGED"
cp -a "$TMP/bin" "$TMP/share" "$TMP/SHA256SUMS" "$STAGED/"
[[ -d "$TMP/lib" ]] && cp -a "$TMP/lib" "$STAGED/"
[[ -d "$TMP/libexec" ]] && cp -a "$TMP/libexec" "$STAGED/"
python3 - "$STAGED" "$ARCHIVE" <<'PY'
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

root = Path(sys.argv[1])
manifest = {
    "schema": "chimera-verified-desktop-compat-tools/v1",
    "source_archive": Path(sys.argv[2]).name,
    "imported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "execution_scope": "Linux host compatibility bundle; not a Koronos-native executable set",
    "sha256_manifest": "SHA256SUMS",
    "directories": ["bin", "share", "lib (optional)", "libexec (optional)"],
}
(root / "IMPORT-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY
rm -rf "$DEST"
mv "$STAGED" "$DEST"
trap - EXIT
rm -rf "$TMP"
printf 'Verified desktop compatibility tools imported to: %s\n' "$DEST"
printf 'Use CHIMERA_DESKTOP_COMPAT_TOOLS_DIR=%q with the ISO builder.\n' "$DEST"
