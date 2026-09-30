#!/bin/sh
set -eu
DEST=${1:?destination root required}
SRC=${2:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}
mkdir -p "$DEST/etc/chimera/drivers" "$DEST/var/log/mesgs/archive" "$DEST/var/log/chimera" "$DEST/usr/bin" "$DEST/usr/share/applications" "$DEST/usr/share/chimera/kore" "$DEST/etc/systemd/system"
ln -sfn /var/log/mesgs "$DEST/var/log/chimera/mesgs" 2>/dev/null || true
ln -sfn mesgs "$DEST/var/log/messages" 2>/dev/null || true
for f in chimera-logd.sh chimera-logrotate.sh chimera-driver-manager.sh chimera-kmsg-forwarder.sh chimera-xexec.sh chimera-playstation-center.sh chimera-crash-dump.sh chimera-screen-of-death.sh chimera-memory-dump.sh chimera-rom-search.sh chimera-game-center.sh chimera-free-3d-games.sh; do
  [ -f "$SRC/tools/$f" ] && cp -f "$SRC/tools/$f" "$DEST/usr/bin/$f" && chmod +x "$DEST/usr/bin/$f"
done
[ -f "$SRC/tools/chimera-driver-center.sh" ] && cp -f "$SRC/tools/chimera-driver-center.sh" "$DEST/usr/bin/chimera-driver-center" && chmod +x "$DEST/usr/bin/chimera-driver-center"
[ -f "$SRC/system/aurora/chimera-driver-center.desktop" ] && cp -f "$SRC/system/aurora/chimera-driver-center.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/system/aurora/chimera-playstation.desktop" ] && cp -f "$SRC/system/aurora/chimera-playstation.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/system/aurora/chimera-rom-search.desktop" ] && cp -f "$SRC/system/aurora/chimera-rom-search.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/system/aurora/chimera-game-center.desktop" ] && cp -f "$SRC/system/aurora/chimera-game-center.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/system/aurora/chimera-free-3d-games.desktop" ] && cp -f "$SRC/system/aurora/chimera-free-3d-games.desktop" "$DEST/usr/share/applications/"
[ -f "$SRC/system/aurora/game-center-panel.json" ] && cp -f "$SRC/system/aurora/game-center-panel.json" "$DEST/usr/share/chimera/aurora/"
[ -f "$SRC/config/aurora/game-center.json" ] && cp -f "$SRC/config/aurora/game-center.json" "$DEST/usr/share/chimera/aurora/config/"
[ -f "$SRC/config/aurora/free-3d-games.json" ] && cp -f "$SRC/config/aurora/free-3d-games.json" "$DEST/usr/share/chimera/aurora/config/"
mkdir -p "$DEST/usr/share/chimera/aurora/config"
[ -f "$SRC/config/aurora/rom-search.json" ] && cp -f "$SRC/config/aurora/rom-search.json" "$DEST/usr/share/chimera/aurora/config/"
[ -f "$SRC/system/kore/chimera-runtime-services.json" ] && cp -f "$SRC/system/kore/chimera-runtime-services.json" "$DEST/usr/share/chimera/kore/"
[ -f "$SRC/system/aurora/chimera-crash-screen.json" ] && cp -f "$SRC/system/aurora/chimera-crash-screen.json" "$DEST/usr/share/chimera/aurora/"
[ -f "$SRC/config/crash/chimera-crash-policy.json" ] && mkdir -p "$DEST/etc/chimera" && cp -f "$SRC/config/crash/chimera-crash-policy.json" "$DEST/etc/chimera/"
[ -f "$SRC/config/drivers/driver-repositories.json" ] && cp -f "$SRC/config/drivers/driver-repositories.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/config/drivers/driver-policy.json" ] && cp -f "$SRC/config/drivers/driver-policy.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/system/boot/chimera-logging.conf" ] && cp -f "$SRC/system/boot/chimera-logging.conf" "$DEST/etc/chimera/logging.conf"
for f in system/logging/chimera-logd.service system/logging/chimera-logrotate.service system/logging/chimera-logrotate.timer system/drivers/chimera-driver-manager.service system/logging/chimera-kmsg-forwarder.service system/crash/chimera-crash.service; do
  [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$DEST/etc/systemd/system/"
done
