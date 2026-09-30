#!/bin/sh
set -eu
DEST=${1:?destination root required}
SRC=${2:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}
mkdir -p "$DEST/etc/chimera/drivers" "$DEST/var/log/mesgs/archive" "$DEST/var/log/chimera" "$DEST/usr/bin" "$DEST/usr/share/applications" "$DEST/etc/systemd/system"
ln -sfn /var/log/mesgs "$DEST/var/log/chimera/mesgs" 2>/dev/null || true
ln -sfn mesgs "$DEST/var/log/messages" 2>/dev/null || true
for f in chimera-logd.sh chimera-logrotate.sh chimera-driver-manager.sh; do
  [ -f "$SRC/tools/$f" ] && cp -f "$SRC/tools/$f" "$DEST/usr/bin/$f" && chmod +x "$DEST/usr/bin/$f"
done
[ -f "$SRC/tools/chimera-driver-center.sh" ] && cp -f "$SRC/tools/chimera-driver-center.sh" "$DEST/usr/bin/chimera-driver-center" && chmod +x "$DEST/usr/bin/chimera-driver-center"
[ -f "$SRC/system/aurora/chimera-driver-center.desktop" ] && cp -f "$SRC/system/aurora/chimera-driver-center.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/config/drivers/driver-repositories.json" ] && cp -f "$SRC/config/drivers/driver-repositories.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/config/drivers/driver-policy.json" ] && cp -f "$SRC/config/drivers/driver-policy.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/system/boot/chimera-logging.conf" ] && cp -f "$SRC/system/boot/chimera-logging.conf" "$DEST/etc/chimera/logging.conf"
for f in system/logging/chimera-logd.service system/logging/chimera-logrotate.service system/logging/chimera-logrotate.timer system/drivers/chimera-driver-manager.service; do
  [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$DEST/etc/systemd/system/"
done
