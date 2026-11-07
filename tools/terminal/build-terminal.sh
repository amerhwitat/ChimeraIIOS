#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$ROOT/rootfs"
if [ -n "${CHIMERA_ROOTFS_DIR:-}" ]; then DEST="$CHIMERA_ROOTFS_DIR"; fi
install -Dm0755 "$ROOT/tools/terminal/chimera_terminald.py" "$DEST/usr/lib/chimera/chimera_terminald.py"
install -Dm0755 "$ROOT/tools/terminal/chimera-terminal" "$DEST/usr/bin/chimera-terminal"
install -Dm0755 "$ROOT/tools/terminal/chimera-sql" "$DEST/usr/bin/chimera-sql"
install -Dm0644 "$ROOT/system/terminal/shell_adapters.json" "$DEST/etc/chimera/terminal/shell_adapters.json"
install -Dm0644 "$ROOT/system/terminal/permissions.json" "$DEST/etc/chimera/terminal/permissions.json"
install -Dm0644 "$ROOT/system/terminal/terminal-service.json" "$DEST/etc/chimera/terminal/terminal-service.json"
install -Dm0644 "$ROOT/system/terminal/chimera-terminald.service" "$DEST/etc/systemd/system/chimera-terminald.service"
install -d "$DEST/etc/systemd/system/multi-user.target.wants"
ln -sfn ../chimera-terminald.service "$DEST/etc/systemd/system/multi-user.target.wants/chimera-terminald.service"
cat > "$DEST/usr/bin/terminald" <<'TERMINALD'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/chimera/chimera_terminald.py "$@"
TERMINALD
chmod 0755 "$DEST/usr/bin/terminald"
install -d "$DEST/var/lib/chimera/sandboxes" "$DEST/run/chimera"
if chroot "$DEST" getent group chimera-terminal >/dev/null 2>&1; then :; else chroot "$DEST" groupadd --system chimera-terminal; fi
if chroot "$DEST" getent passwd chimera-terminal >/dev/null 2>&1; then :; else chroot "$DEST" useradd --system --gid chimera-terminal --home-dir /var/lib/chimera/sandboxes --shell /usr/sbin/nologin --no-create-home chimera-terminal; fi
if chroot "$DEST" getent passwd live >/dev/null 2>&1; then chroot "$DEST" usermod -aG chimera-terminal live; fi
echo "[CHIMERA-TERMINAL] staged PTY service, SQL engine and policy"
