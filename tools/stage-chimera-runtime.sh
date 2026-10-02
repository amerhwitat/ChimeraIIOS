#!/bin/sh
set -eu
DEST=${1:?destination root required}
SRC=${2:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)}
mkdir -p "$DEST/etc/chimera/drivers" "$DEST/var/log/mesgs/archive" "$DEST/var/log/chimera" "$DEST/usr/bin" "$DEST/usr/share/applications" "$DEST/usr/share/chimera/kore" "$DEST/usr/share/chimera/aurora" "$DEST/usr/share/chimera/aurora/assets" "$DEST/usr/share/chimera/aurora/config" "$DEST/usr/share/chimera/aurora/emulators/bin" "$DEST/usr/share/chimera/aurora/emulators/desktop" "$DEST/usr/share/chimera/aurora/labwc" "$DEST/usr/share/chimera/aurora/waybar" "$DEST/usr/share/chimera/mobile" "$DEST/etc/systemd/system" "$DEST/etc/xdg/xdg-desktop-portal"
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
[ -f "$SRC/config/aurora/rom-search.json" ] && cp -f "$SRC/config/aurora/rom-search.json" "$DEST/usr/share/chimera/aurora/config/"
[ -f "$SRC/system/kore/chimera-runtime-services.json" ] && cp -f "$SRC/system/kore/chimera-runtime-services.json" "$DEST/usr/share/chimera/kore/"
[ -f "$SRC/system/aurora/chimera-crash-screen.json" ] && cp -f "$SRC/system/aurora/chimera-crash-screen.json" "$DEST/usr/share/chimera/aurora/"
[ -f "$SRC/config/crash/chimera-crash-policy.json" ] && cp -f "$SRC/config/crash/chimera-crash-policy.json" "$DEST/etc/chimera/"
[ -f "$SRC/config/drivers/driver-repositories.json" ] && cp -f "$SRC/config/drivers/driver-repositories.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/config/drivers/driver-policy.json" ] && cp -f "$SRC/config/drivers/driver-policy.json" "$DEST/etc/chimera/drivers/"
[ -f "$SRC/system/boot/chimera-logging.conf" ] && cp -f "$SRC/system/boot/chimera-logging.conf" "$DEST/etc/chimera/logging.conf"

for f in aurora-session.sh aurora-start.sh aurora-desktop-init.sh aurora-progress.sh aurora-event-sound.sh aurora-init-splash.sh; do
  if [ -f "$SRC/desktop/aurora/$f" ]; then
    cp -f "$SRC/desktop/aurora/$f" "$DEST/usr/share/chimera/aurora/$f"
    chmod +x "$DEST/usr/share/chimera/aurora/$f"
  fi
done
for f in rc.xml menu.xml environment autostart; do
  [ -f "$SRC/desktop/aurora/labwc/$f" ] && cp -f "$SRC/desktop/aurora/labwc/$f" "$DEST/usr/share/chimera/aurora/labwc/$f"
done
[ -f "$SRC/desktop/aurora/waybar/config.jsonc" ] && cp -f "$SRC/desktop/aurora/waybar/config.jsonc" "$DEST/usr/share/chimera/aurora/waybar/"
[ -f "$SRC/desktop/aurora/waybar/style.css" ] && cp -f "$SRC/desktop/aurora/waybar/style.css" "$DEST/usr/share/chimera/aurora/waybar/"
[ -f "$SRC/desktop/aurora/xdg-desktop-portal/aurora-portals.conf" ] && cp -f "$SRC/desktop/aurora/xdg-desktop-portal/aurora-portals.conf" "$DEST/etc/xdg/xdg-desktop-portal/aurora-portals.conf"

# Generate optional Aurora initialization media and menu sounds at build time.
if [ -x "$SRC/tools/generate-aurora-media.sh" ]; then
  "$SRC/tools/generate-aurora-media.sh" "$SRC/desktop/aurora/assets" || true
fi

# Hard-code repository-side Aurora artwork and generated media into the installed rootfs.
for f in "$SRC/desktop/aurora/assets"/*; do
  [ -f "$f" ] || continue
  cp -f "$f" "$DEST/usr/share/chimera/aurora/assets/"
done
if [ -d "$SRC/desktop/aurora/assets/sounds" ]; then
  mkdir -p "$DEST/usr/share/chimera/aurora/assets/sounds"
  for f in "$SRC/desktop/aurora/assets/sounds"/*; do [ -f "$f" ] && cp -f "$f" "$DEST/usr/share/chimera/aurora/assets/sounds/"; done
fi
[ -f "$SRC/desktop/aurora/assets/sounds/manifest.json" ] && cp -f "$SRC/desktop/aurora/assets/sounds/manifest.json" "$DEST/usr/share/chimera/aurora/assets/sounds/"
[ -f "$SRC/desktop/aurora/assets/library-artwork-manifest.json" ] && cp -f "$SRC/desktop/aurora/assets/library-artwork-manifest.json" "$DEST/usr/share/chimera/aurora/"
[ -f "$SRC/desktop/aurora/menu-event-map.json" ] && cp -f "$SRC/desktop/aurora/menu-event-map.json" "$DEST/usr/share/chimera/aurora/"
[ -f "$SRC/system/boot/koronos-progress.sh" ] && cp -f "$SRC/system/boot/koronos-progress.sh" "$DEST/usr/share/chimera/aurora/koronos-progress.sh" && chmod +x "$DEST/usr/share/chimera/aurora/koronos-progress.sh"
for bg in "$SRC/desktop/aurora/assets/aurora-wayland-glass.png" "$SRC/desktop/aurora/assets/aurora-wayland-glass.svg" "$SRC/desktop/aurora/assets/aurora-desktop.svg"; do
  if [ -f "$bg" ]; then
    cp -f "$bg" "$DEST/usr/share/chimera/aurora/$(basename "$bg")"
    break
  fi
done

[ -f "$SRC/mobile/mobile-progress.json" ] && cp -f "$SRC/mobile/mobile-progress.json" "$DEST/usr/share/chimera/mobile/"
[ -f "$SRC/mobile/README.md" ] && cp -f "$SRC/mobile/README.md" "$DEST/usr/share/chimera/mobile/"

for f in aurora-emulator-window.sh launch-retro.sh launch-sakhr-ax170.sh launch-sakhr-ax230.sh; do
  if [ -f "$SRC/aurora/emulators/bin/$f" ]; then
    cp -f "$SRC/aurora/emulators/bin/$f" "$DEST/usr/share/chimera/aurora/emulators/bin/$f"
    chmod +x "$DEST/usr/share/chimera/aurora/emulators/bin/$f"
  fi
done
for f in "$SRC/aurora/emulators/desktop"/*.desktop; do
  [ -f "$f" ] || continue
  cp -f "$f" "$DEST/usr/share/chimera/aurora/emulators/desktop/"
  cp -f "$f" "$DEST/usr/share/applications/"
done

for f in system/logging/chimera-logd.service system/logging/chimera-logrotate.service system/logging/chimera-logrotate.timer system/drivers/chimera-driver-manager.service system/logging/chimera-kmsg-forwarder.service system/crash/chimera-crash.service; do
  [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$DEST/etc/systemd/system/"
done

if [ -x "$SRC/tools/provision-aurora-rootfs.sh" ]; then
  AURORA_PROVISION_LOG="${AURORA_PROVISION_LOG:-$DEST/var/log/aurora-provision.log}" \
    "$SRC/tools/provision-aurora-rootfs.sh" "$DEST"
fi

mkdir -p "$DEST/etc/systemd/system/getty@tty1.service.d"
cat > "$DEST/etc/systemd/system/getty@tty1.service.d/aurora-autologin.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin chimera --noclear %I $TERM
EOF
mkdir -p "$DEST/home/chimera"
cat > "$DEST/home/chimera/.bash_profile" <<'EOF'
if [ -z "${AURORA_SESSION_STARTED:-}" ] && [ "$(tty 2>/dev/null || true)" = "/dev/tty1" ]; then
  export AURORA_SESSION_STARTED=1
  exec /usr/share/chimera/aurora/aurora-start.sh
fi
EOF
cat > "$DEST/home/chimera/.profile" <<'EOF'
[ -f "$HOME/.bash_profile" ] && . "$HOME/.bash_profile"
EOF
chroot "$DEST" /bin/chown -R chimera:chimera /home/chimera 2>/dev/null || true
chmod 0644 "$DEST/home/chimera/.bash_profile" "$DEST/home/chimera/.profile"

mkdir -p "$DEST/usr/share/wayland-sessions"
cat > "$DEST/usr/share/wayland-sessions/aurora.desktop" <<'EOF'
[Desktop Entry]
Name=Aurora Wayland
Comment=Chimera II Aurora Desktop
Exec=/usr/share/chimera/aurora/aurora-start.sh
Type=Application
DesktopNames=Aurora;Chimera
EOF
