#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/provision-aurora-rootfs.sh

Usage:
  tools/provision-aurora-rootfs.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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

HOST_RESOLV=/etc/resolv.conf
ROOT_RESOLV="$DEST/etc/resolv.conf"
RESOLV_BACKUP="$DEST/etc/resolv.conf.chimera-backup"
if [ -r "$HOST_RESOLV" ]; then
  if ! grep -Eq '^nameserver[[:space:]]+[^[:space:]]+$' "$ROOT_RESOLV" 2>/dev/null || \
     grep -Eq '^nameserver[[:space:]]+(127\\.|::1$)' "$ROOT_RESOLV" 2>/dev/null; then
    rm -f "$RESOLV_BACKUP"
    if [ -e "$ROOT_RESOLV" ] || [ -L "$ROOT_RESOLV" ]; then
      cp -a "$ROOT_RESOLV" "$RESOLV_BACKUP" 2>/dev/null || true
      rm -f "$ROOT_RESOLV"
    fi
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

# Professional terminal and desktop utilities are optional so a reduced image
# can still boot Aurora. zenity provides the GUI progress dialog; the progress
# script automatically falls back to its terminal renderer if it is absent.
for pkg in xdg-desktop-portal-gtk alacritty kitty terminator wofi slurp zenity; do
  install_if_available "$pkg" || true
done

for pkg in firefox pcmanfm-qt gnome-text-editor pavucontrol btop; do
  install_if_available "$pkg" || echo "[Aurora][WARN] optional client unavailable: $pkg"
done

if ! chroot "$DEST" /usr/bin/id -u chimera >/dev/null 2>&1; then
  chroot "$DEST" /usr/sbin/useradd -m -s /bin/bash -U chimera
fi
for group in audio video render input plugdev netdev; do
  if chroot "$DEST" /usr/bin/getent group "$group" >/dev/null 2>&1; then
    chroot "$DEST" /usr/sbin/usermod -aG "$group" chimera || true
  fi
done

chroot "$DEST" /usr/bin/apt-get clean
rm -rf "$DEST/var/lib/apt/lists/"*
if [ -e "$RESOLV_BACKUP" ] || [ -L "$RESOLV_BACKUP" ]; then
  rm -f "$ROOT_RESOLV"
  mv -f "$RESOLV_BACKUP" "$ROOT_RESOLV"
fi

echo "[Aurora] Provisioning complete"
