#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: test-native-chimera-tools.sh ROOTFS}"
for tool in chmctl chimeractl chimera-info chimera-doctor chimera-update chimera-package korectl chimera-service chimera-asm chimera-disasm; do
  chroot "$ROOTFS" /bin/sh -c "command -v '$tool' >/dev/null 2>&1" || {
    echo "Missing real hosted Chimera tool: $tool" >&2; exit 1;
  }
done
info="$(chroot "$ROOTFS" /usr/bin/chimera-info)"
grep -q '^Kernel:' <<<"$info"
grep -q '^Machine:' <<<"$info"
doctor="$(chroot "$ROOTFS" /usr/bin/chimera-doctor)"
python3 - "$doctor" <<'PY'
import json,sys
lines=sys.argv[1].splitlines()
data=json.loads(lines[-1])
assert data["koronos_runtime"]=="not-certified-by-hosted-linux-diagnostics"
PY
chroot "$ROOTFS" /usr/bin/chimera-update --help >/dev/null
chroot "$ROOTFS" /usr/bin/korectl --help >/dev/null
chroot "$ROOTFS" /usr/bin/chmctl status >/dev/null
chroot "$ROOTFS" /usr/bin/chimeractl status >/dev/null
work="$ROOTFS/tmp/chimera-native-tool-smoke"
mkdir -p "$work"
printf 'NOP\n' > "$work/input.asm"
chroot "$ROOTFS" /usr/bin/chimera-asm /tmp/chimera-native-tool-smoke/input.asm /tmp/chimera-native-tool-smoke/output.chm
test -s "$work/output.chm"
disassembly="$(chroot "$ROOTFS" /usr/bin/chimera-disasm /tmp/chimera-native-tool-smoke/output.chm)"
grep -q 'NOP' <<<"$disassembly"
rm -rf "$work"
echo "PASS: real Chimera diagnostics, package/update, Kore and assembler frontends execute in the hosted target rootfs."
