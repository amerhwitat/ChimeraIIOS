#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
BUILD="$ROOT/build-chimera-iso.sh"
JASPER="$ROOT/boot/jasper/install.cfg"
ISO="$ROOT/iso/chimera-live-iso.sh"

grep -q '/install/installer/installation.img' "$JASPER"
grep -q '/install/installer/installation-manifest.json' "$JASPER"
grep -q 'installation.img' "$BUILD"
grep -q 'installation-manifest.json' "$BUILD"
grep -q 'installer-initrd.img' "$BUILD"
grep -q 'live-manifest.json' "$ISO"
grep -q '  -R' "$ISO"

bash -n "$BUILD"
bash -n "$ISO"
echo "installation media contract: OK"
