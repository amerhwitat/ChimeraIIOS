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

# Docker export intentionally removes apt lists. Recreate them inside the
# target rootfs so Aurora is built into the ISO rather than installed at first
# boot. DNS is inherited from the exported Ubuntu container when available.
if ! chroot "$DEST" /usr/bin/apt-get update -o Acquire::Retries=5; then
  echo "[Aurora][ERROR] apt-get update failed inside rootfs"
  exit 1
fi

install_if_available() {
  pkg=$1
  if chroot "$DEST" /usr/bin/apt-cache policy "$pkg" 2>/dev/null | grep -q '^  Candidate:'; then
    echo "[Aurora] installing $pkg"
    chroot "$DEST" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
      /usr/bin/apt-get install -y --no-install-recommends "$pkg"
  else
    echo "[Aurora][WARN] package unavailable: $pkg"
  fi
}

# Core compositor/session path. labwc is the Aurora compositor layer; it is
# deliberately used instead of pretending the current research launcher is a
# compositor. Ubuntu 24.04 ships labwc for amd64/arm64 and it uses wlroots.
for pkg in \
  labwc waybar xwayland dbus-user-session \
  pipewire wireplumber pipewire-pulse \
  xdg-desktop-portal xdg-desktop-portal-wlr \
  swaybg swayidle mako-notifier wl-clipboard wlr-randr \
  foot fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji \
  network-manager policykit-1; do
  install_if_available "$pkg"
done

# Useful desktop clients. Missing optional packages must not prevent the ISO
# from booting into the compositor.
for pkg in firefox pcmanfm-qt gnome-text-editor pavucontrol; do
  install_if_available "$pkg" || echo "[Aurora][WARN] optional client failed: $pkg"
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

# Do not leave apt metadata in the ISO rootfs.
chroot "$DEST" /usr/bin/apt-get clean
rm -rf "$DEST/var/lib/apt/lists/"*

echo "[Aurora] Provisioning complete"
