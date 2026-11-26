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

# grub-mkrescue forwards post-`--` arguments to xorriso in native command
# mode. The mkisofs compatibility flags -R/-J are rejected there; the
# supported switches are -rockridge on and -joliet on.
grep -Fq 'xorriso_opts=( -rockridge on -joliet on )' "$script" || {
    echo "FAIL: build-chimera-iso.sh lacks supported xorriso Rock Ridge/Joliet switches"
    exit 1
}

grep -Fq '"${xorriso_opts[@]}"' "$script" || {
    echo "FAIL: build-chimera-iso.sh does not pass xorriso_opts to grub-mkrescue"
    exit 1
}

if grep -Eq 'xorriso_opts=.*[[:space:]]-R[[:space:]]' "$script"; then
    echo "FAIL: build-chimera-iso.sh uses unsupported mkisofs -R flag"
    exit 1
fi
if grep -Eq 'xorriso_opts=.*[[:space:]]-J[[:space:]]' "$script"; then
    echo "FAIL: build-chimera-iso.sh uses unsupported mkisofs -J flag"
    exit 1
fi


echo "PASS: xorriso native options use supported Rock Ridge/Joliet switches"
