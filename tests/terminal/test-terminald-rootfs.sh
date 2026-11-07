#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="\${1:?usage: test-terminald-rootfs.sh ROOTFS}"
for path in \
  usr/lib/chimera/chimera_terminald.py \
  usr/bin/terminald usr/bin/chimera-terminal usr/bin/chimera-sql \
  usr/bin/bwrap etc/chimera/terminal/shell_adapters.json \
  etc/chimera/terminal/permissions.json etc/chimera/terminal/terminal-service.json \
  etc/systemd/system/chimera-terminald.service \
  etc/systemd/system/multi-user.target.wants/chimera-terminald.service \
  etc/chimera/terminal/auth.token; do
  test -s "$ROOTFS/$path" || { echo "missing terminal runtime asset: $path" >&2; exit 1; }
done
chroot "$ROOTFS" /usr/bin/python3 -m py_compile /usr/lib/chimera/chimera_terminald.py
chroot "$ROOTFS" /usr/bin/python3 -c 'import json; c=json.load(open("/etc/chimera/terminal/terminal-service.json")); assert c["sandbox"]["required"] is True and c["sandbox"]["allow_unsafe_host"] is False'
chroot "$ROOTFS" /usr/bin/terminald --help >/dev/null
chroot "$ROOTFS" /usr/bin/chimera-terminal --help >/dev/null
chroot "$ROOTFS" /usr/bin/bwrap --version >/dev/null
socket="$ROOTFS/run/chimera/terminald-test.sock"
set +e
timeout 2s chroot "$ROOTFS" /usr/bin/terminald --socket /run/chimera/terminald-test.sock --config /etc/chimera/terminal/terminal-service.json >/dev/null 2>&1
status=$?
set -e
[[ "$status" == 124 || "$status" == 137 ]] || { echo "terminald failed to stay running (status $status)" >&2; exit 1; }
test -S "$socket"
rm -f "$socket"
chroot "$ROOTFS" getent group chimera-terminal >/dev/null
chroot "$ROOTFS" id -Gn live | tr ' ' '\n' | grep -qx chimera-terminal
test "$(stat -c '%a' "$ROOTFS/etc/chimera/terminal/auth.token")" = 640
test "$(chroot "$ROOTFS" stat -c '%G' /etc/chimera/terminal/auth.token)" = chimera-terminal
echo "PASS terminald service, sandbox binary, config, token permissions and live-user group membership"
