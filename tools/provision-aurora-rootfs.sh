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

# Restore the rootfs resolver even when apt or dpkg fails. A failed optional
# provisioning attempt must not leave a build rootfs pointing at host DNS.
restore_resolver() {
  if [ -n "${RESOLV_BACKUP:-}" ] && { [ -e "$RESOLV_BACKUP" ] || [ -L "$RESOLV_BACKUP" ]; }; then
    rm -f "${ROOT_RESOLV:-}" 2>/dev/null || true
    mv -f "$RESOLV_BACKUP" "$ROOT_RESOLV" 2>/dev/null || true
  elif [ -n "${RESOLV_ABSENT_MARKER:-}" ] && [ -e "$RESOLV_ABSENT_MARKER" ]; then
    rm -f "${ROOT_RESOLV:-}" "$RESOLV_ABSENT_MARKER" 2>/dev/null || true
  fi
}
trap restore_resolver EXIT

echo "[Aurora] Provisioning Wayland desktop runtime into $DEST"

[ -x "$DEST/usr/bin/apt-get" ] || {
  echo "[Aurora][ERROR] rootfs has no apt-get"
  exit 1
}

HOST_RESOLV=/etc/resolv.conf
ROOT_RESOLV="$DEST/etc/resolv.conf"
RESOLV_BACKUP="$DEST/etc/resolv.conf.chimera-backup"
RESOLV_ABSENT_MARKER="$DEST/etc/.chimera-resolv-conf-was-absent"
if [ -r "$HOST_RESOLV" ]; then
  if ! grep -Eq '^nameserver[[:space:]]+[^[:space:]]+$' "$ROOT_RESOLV" 2>/dev/null || \
     grep -Eq '^nameserver[[:space:]]+(127\.|::1$)' "$ROOT_RESOLV" 2>/dev/null; then
    rm -f "$RESOLV_BACKUP" "$RESOLV_ABSENT_MARKER"
    if [ -e "$ROOT_RESOLV" ] || [ -L "$ROOT_RESOLV" ]; then
      cp -a "$ROOT_RESOLV" "$RESOLV_BACKUP" 2>/dev/null || true
      rm -f "$ROOT_RESOLV"
    else
      : > "$RESOLV_ABSENT_MARKER"
    fi
    awk '/^nameserver[[:space:]]+/ && $2 !~ /^(127\.|::1$)/ {print}' "$HOST_RESOLV" > "$ROOT_RESOLV" || true
    if ! grep -q '^nameserver' "$ROOT_RESOLV" 2>/dev/null; then
      printf '%s\n' 'nameserver 1.1.1.1' 'nameserver 8.8.8.8' > "$ROOT_RESOLV"
    fi
  fi
fi

# Prefer fresh indexes, but do not throw away a usable cached package
# database merely because a mirror is temporarily unavailable. In fallback
# mode apt is forbidden from downloading: it may only install packages already
# present in the rootfs archive cache. Missing cache entries remain explicit
# failures for required packages and are never represented as installed.
offline_mode=0
if ! chroot "$DEST" /usr/bin/apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30; then
  cached_candidate=$(chroot "$DEST" /usr/bin/apt-cache policy labwc 2>/dev/null | awk '$1=="Candidate:" {print $2; exit}')
  if [ -n "$cached_candidate" ] && [ "$cached_candidate" != "(none)" ]; then
    offline_mode=1
    echo "[Aurora][WARN] apt-get update failed; using cached package indexes and archive files only."
  else
    echo "[Aurora][ERROR] apt-get update failed and no usable cached package index exists."
    exit 1
  fi
fi

install_if_available() {
  pkg=$1
  candidate=$(chroot "$DEST" /usr/bin/apt-cache policy "$pkg" 2>/dev/null | awk '$1=="Candidate:" {print $2; exit}')
  if [ -n "$candidate" ] && [ "$candidate" != "(none)" ]; then
    echo "[Aurora] installing $pkg"
    if [ "$offline_mode" -eq 1 ]; then
      chroot "$DEST" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
        /usr/bin/apt-get install -y --no-install-recommends --no-download "$pkg"
    else
      chroot "$DEST" /usr/bin/env DEBIAN_FRONTEND=noninteractive \
        /usr/bin/apt-get install -y --no-install-recommends "$pkg"
    fi
  else
    echo "[Aurora][WARN] package unavailable in configured indexes: $pkg"
    return 1
  fi
}

required_failed=0
for pkg in \
  labwc waybar xwayland dbus-user-session \
  pipewire wireplumber pipewire-pulse \
  xdg-desktop-portal xdg-desktop-portal-wlr \
  swaybg swayidle mako wl-clipboard wlr-randr \
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
