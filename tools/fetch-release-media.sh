#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/releases}"
TAG="${CHIMERA_RELEASE_TAG:-latest}"
mkdir -p "$OUT"
command -v gh >/dev/null 2>&1 || { echo "GitHub CLI (gh) is required to fetch release media." >&2; exit 2; }
if [[ "$TAG" == "latest" ]]; then gh release download --repo amerhwitat/ChimeraIIOS --pattern "chimera-ii-os.iso" --dir "$OUT" --clobber; gh release download --repo amerhwitat/ChimeraIIOS --pattern "*spitfire*.img" --dir "$OUT" --clobber || true; else gh release download "$TAG" --repo amerhwitat/ChimeraIIOS --pattern "chimera-ii-os.iso" --dir "$OUT" --clobber; gh release download "$TAG" --repo amerhwitat/ChimeraIIOS --pattern "*spitfire*.img" --dir "$OUT" --clobber || true; fi
echo "Release media staged in $OUT"
