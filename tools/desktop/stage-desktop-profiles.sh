#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="${ROOT}/desktop/profiles/desktop-profiles.json"
OUT="${1:-${ROOT}/build/rootfs/usr/share/chimera/desktop-profiles}"
MODE="${CHIMERA_DESKTOP_MODE:-aurora}"
mkdir -p "$OUT"

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required" >&2; exit 127; }
[[ -f "$MANIFEST" ]] || { echo "ERROR: desktop profile manifest missing: $MANIFEST" >&2; exit 2; }

cp -f "$MANIFEST" "$OUT/desktop-profiles.json"
python3 - "$MANIFEST" "$MODE" "$OUT/selected-profile.json" <<'PY'
import json, sys
manifest, mode, output = sys.argv[1:]
data = json.load(open(manifest, encoding='utf-8'))
profiles = {p['id']: p for p in data['profiles']}
if mode not in profiles:
    raise SystemExit(f"unknown desktop profile: {mode}")
json.dump(profiles[mode], open(output, 'w', encoding='utf-8'), indent=2)
PY

# Only install/package open-source Linux components available from the target
# distribution. Windows/macOS profiles are personalities/compatibility layers;
# proprietary Microsoft/Apple binaries and artwork are never copied into ISO.
if [[ "${CHIMERA_STAGE_DESKTOP_BINARIES:-0}" == 1 ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "[desktop] package staging is distribution-specific; use the profile's package list with the rootfs package manager."
  fi
fi

echo "[desktop] staged profile: $MODE"
