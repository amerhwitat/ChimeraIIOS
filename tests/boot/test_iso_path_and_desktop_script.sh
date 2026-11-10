#!/usr/bin/env bash
set -euo pipefail
bash -n tools/build-desktop-binaries.sh
grep -Fq 'extract /boot/grub/grub.cfg' .github/workflows/chimera-iso.yml
grep -Fq 'python3 tests/boot/test_production_target_handoff_qemu.py' .github/workflows/chimera-full-iso.yml
echo "Desktop build shell syntax and extracted GRUB/userspace verification contracts: PASS"
