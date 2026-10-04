#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/tests/test-xorriso-mkrescue-options.sh

Usage:
  tools/tests/test-xorriso-mkrescue-options.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$SCRIPT_DIR/build-chimera-iso.sh"

# xorriso's mkisofs emulation supports -R/-r for Rock Ridge, not -rockridge.
# Keep the build script limited to options documented by xorriso.
if grep -Eq 'local xorriso_opts=.*-rockridge' "$script"; then
    echo "FAIL: build-chimera-iso.sh passes unsupported -rockridge to xorriso"
    exit 1
fi

grep -Eq 'local xorriso_opts=.*-R([[:space:]]|[-])' "$script" || {
    echo "FAIL: build-chimera-iso.sh does not enable Rock Ridge with supported -R"
    exit 1
}

grep -Eq 'local xorriso_opts=.*-J([[:space:]]|[-])' "$script" || {
    echo "FAIL: build-chimera-iso.sh does not enable Joliet with supported -J"
    exit 1
}

echo "PASS: xorriso mkisofs options use supported Rock Ridge/Joliet flags"
