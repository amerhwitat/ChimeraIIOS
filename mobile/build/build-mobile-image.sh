#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROFILE="${1:-$ROOT/mobile/device-profiles/reference-aarch64.json}"
OUT="${2:-$ROOT/mobile/images/dist}"
python3 "$ROOT/mobile/build/validate-profile.py" "$PROFILE"
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$PROFILE" "$OUT/device-profile.json"
printf 'Chimera Mobile research image layout prepared at %s\n' "$OUT"
printf '%s\n' 'This stage intentionally stops before device flashing/signing.'
printf '%s\n' 'A production image requires the exact device kernel/vendor modules and authorized AVB signing keys.'
