#!/usr/bin/env bash
set -euo pipefail
bash -n tools/build-desktop-binaries.sh
grep -Fq 'boot/iso/dist/iso/boot/grub/grub.cfg' .github/workflows/chimera-iso.yml
if grep -Fq 'boot/iso/dist/iso/boot/grub.cfg' .github/workflows/chimera-iso.yml; then
  echo "Obsolete GRUB config path remains in the ISO verifier" >&2
  exit 1
fi
echo "Desktop build shell syntax and GRUB staging path: PASS"
