#!/usr/bin/env bash
set -euo pipefail
echo "Chimera II host execution capabilities"
printf 'Host: '; uname -srm 2>/dev/null || true
for c in qemu-system-x86_64 qemu-system-aarch64 qemu-system-riscv64 qemu-img; do
 command -v "$c" >/dev/null 2>&1 && echo "$c: installed" || echo "$c: missing"
done
[[ "$(uname -s)" == "Linux" && -e /dev/kvm ]] && echo "KVM: available" || echo "KVM: not detected"
[[ "$(uname -s)" == "Darwin" ]] && echo "macOS: QEMU HVF may be selected"
[[ "$(uname -s)" =~ MINGW|MSYS|CYGWIN ]] && echo "Windows: QEMU WHPX may be selected"
