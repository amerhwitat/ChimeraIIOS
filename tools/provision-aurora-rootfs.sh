#!/bin/sh
set -eu

DEST=${1:?rootfs destination required}
LOG=${AURORA_PROVISION_LOG:-/tmp/chimera-aurora-provision.log}

mkdir -p "$DEST" "$(dirname "$LOG")"
exec >"$LOG" 2>&1

echo "[Aurora] Provisioning Wayland desktop runtime into $DEST"

[ -x "$DEST/usr/bin/apt-get" ] || {
  echo "[Aurora][ERROR] rootfs has no apt-get"
  exit 1
}

# Docker export does not preserve bind-mounted volume contents. Recreate a
# usable resolver for chrooted apt when the exported /etc/resolv.conf points at
# a host-only loopback resolver (common with systemd-resolved/WSL).
HOST_RESOLV=/etc/resolv.conf
ROOT_RESOLV="$DEST/etc/resolv.conf"
RESOLV_BACKUP="$DEST/etc/resolv.conf.chimera-backup"
if [ -r "$HOST_RESOLV" ]; then
  if ! grep -Eq '^nameserver[[:space:]]+[^[:space:]]+$' "$ROOT_RESOLV" 2>/dev/null || \
     grep -Eq '^nameserver[[:space:]]+(127\\.|::1$)' "$ROOT_RESOLV" 2>/dev/null; then
    cp -a "$ROOT_RESOLV" "$RESOLV_BACKUP" 2>/dev/null || true
    awk '/^nameserver[[:space:]]+/ && $2 !~ /^(127\\.|::1$)/ {print}' "$HOST_RESOLV" > "$ROOT_RESOLV" || true
    if ! grep -q '^nameserver' "$ROOT_RESOLV" 2>/dev/null; then
      printf '%s\n' 'nameserver 1.1.1.1' 'nameserver 8.8.8.8' > "$ROOT_RESOLV"
    fi
  fi
fi

if ! chroot "$DEST" /usr/bin/apt-get update -o Acquire::Retries=5; then
  echo "[Aurora][ERROR] apt-get update failed inside rootfs"
  exit 1
fi

install_if_available() {
  pkg=$1
  candidate=$(chroot "$DEST" /usr/bin/apt-cache policy "$pkg" 2>/dev/null | awk '$1=="Candidate:" {print $2; exit}')
  if [ -n "$candidate" ] && [ "$candidate" != "(none)" ]; then
    echo "[Aurora] installing $pkg"
    chroot "$DEST" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
      /usr/bin/apt-get install -y --no-install-recommends "$pkg"
  else
    echo "[Aurora][WARN] package unavailable: $pkg"
    return 1
  fi
}

# Core compositor/session path. labwc is the Aurora compositor layer; it is
# deliberately used instead of pretending the current research launcher is a
# compositor. Ubuntu 24.04 ships labwc for amd64/arm64 and it uses wlroots.
required_failed=0
for pkg in \
  labwc waybar xwayland dbus-user-session \
  pipewire wireplumber pipewire-pulse \
  xdg-desktop-portal xdg-desktop-portal-wlr \
  swaybg swayidle mako-notifier wl-clipboard wlr-randr \
  foot fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji \
  network-manager policykit-1; do
  install_if_available "$pkg" || required_failed=1
done

if [ "$required_failed" -ne 0 ]; then
  echo "[Aurora][ERROR] one or more required graphical runtime packages are unavailable"
  exit 1
fi

# GTK is a useful fallback portal backend for file chooser/settings surfaces.
# These are optional because wlroots provides the Wayland-specific ScreenCast
# and Screenshot interfaces used by Aurora.
for pkg in xdg-desktop-portal-gtk alacritty kitty terminator; do
  install_if_available "$pkg" || true
done

# Useful desktop clients. Missing optional packages must not prevent the ISO
# from booting into the compositor.
for pkg in firefox pcmanfm-qt gnome-text-editor pavucontrol btop; do
  install_if_available "$pkg" || echo "[Aurora][WARN] optional client unavailable: $pkg"
done

# Dedicated non-root desktop account. The tty1 autologin below creates a real
# PAM/logind session, which is important for DRM/input access and XDG_RUNTIME_DIR.
if ! chroot "$DEST" /usr/bin/id -u chimera >/dev/null 2>&1; then
  chroot "$DEST" /usr/sbin/useradd -m -s /bin/bash -U chimera
fi
for group in audio video render input plugdev netdev; do
  if chroot "$DEST" /usr/bin/getent group "$group" >/dev/null 2>&1; then
    chroot "$DEST" /usr/sbin/usermod -aG "$group" chimera || true
  fi
done

# Do not leave apt metadata in the ISO rootfs. Keep the generated resolver
# only if the target originally needed a synthetic resolver; otherwise restore
# the exported file so runtime systemd-resolved/network management owns it.
chroot "$DEST" /usr/bin/apt-get clean
rm -rf "$DEST/var/lib/apt/lists/"*
if [ -f "$RESOLV_BACKUP" ]; then
  rm -f "$ROOT_RESOLV"
  mv -f "$RESOLV_BACKUP" "$ROOT_RESOLV"
fi

echo "[Aurora] Provisioning complete"
