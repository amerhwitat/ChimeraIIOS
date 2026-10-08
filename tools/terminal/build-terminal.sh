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
install -d "$DEST/var/lib/chimera/sandboxes" "$DEST/run/chimera"
echo "[CHIMERA-TERMINAL] staged PTY service, SQL engine and policy"
