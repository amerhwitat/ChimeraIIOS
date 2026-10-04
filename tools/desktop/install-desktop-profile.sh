#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/desktop/install-desktop-profile.sh

Usage:
  tools/desktop/install-desktop-profile.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

ROOTFS="${1:-}"
PROFILE="${2:-${CHIMERA_DESKTOP_MODE:-aurora}}"
MANIFEST="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/desktop/profiles/desktop-profiles.json"

[[ -n "$ROOTFS" && -d "$ROOTFS" ]] || { echo "usage: $0 ROOTFS PROFILE" >&2; exit 2; }
[[ -f "$MANIFEST" ]] || { echo "ERROR: profile manifest missing" >&2; exit 2; }

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required" >&2; exit 127; }
mapfile -t PACKAGES < <(python3 - "$MANIFEST" "$PROFILE" <<'PY'
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
for p in m['profiles']:
    if p['id']==sys.argv[2]:
        print('\n'.join(p.get('packages', [])))
        break
else:
    raise SystemExit(f"unknown profile: {sys.argv[2]}")
PY
)

if ((${#PACKAGES[@]} == 0)); then
  echo "[desktop] $PROFILE requires no third-party package staging."
  exit 0
fi

# This helper intentionally installs only through the target distribution's
# package manager. It does not copy host /usr binaries into the Chimera ISO.
if [[ -x "$ROOTFS/usr/bin/apt-get" ]]; then
  echo "[desktop] apt-based rootfs detected; install packages in the builder's package stage: ${PACKAGES[*]}"
elif [[ -x "$ROOTFS/usr/bin/pacman" ]]; then
  echo "[desktop] pacman-based rootfs detected; install packages in the builder's package stage: ${PACKAGES[*]}"
elif [[ -x "$ROOTFS/usr/bin/dnf" ]]; then
  echo "[desktop] dnf-based rootfs detected; install packages in the builder's package stage: ${PACKAGES[*]}"
else
  echo "[desktop] no supported package manager found in $ROOTFS"
  exit 3
fi

mkdir -p "$ROOTFS/usr/share/chimera/desktop-profiles"
printf '%s\n' "$PROFILE" > "$ROOTFS/usr/share/chimera/desktop-profiles/selected"
printf '%s\n' "${PACKAGES[@]}" > "$ROOTFS/usr/share/chimera/desktop-profiles/packages.$PROFILE"
echo "[desktop] profile manifest installed; package installation remains distribution/build-stage controlled."
