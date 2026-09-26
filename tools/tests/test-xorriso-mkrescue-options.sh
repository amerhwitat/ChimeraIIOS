#!/usr/bin/env bash
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
