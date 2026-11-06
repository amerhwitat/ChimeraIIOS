#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: install-terminal-shell-suite.sh ROOTFS}"
[[ -d "$ROOTFS" && -x "$ROOTFS/bin/sh" ]] || { echo "invalid target rootfs: $ROOTFS" >&2; exit 2; }
chroot "$ROOTFS" /bin/sh -eu -c '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  installed=""
  missing=""
  install_one() {
    pkg="$1"; bin="$2"
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      apt-get install -y --no-install-recommends "$pkg"
      if command -v "$bin" >/dev/null 2>&1; then
        installed="${installed}${pkg}|${bin}\n"
      else
        missing="${missing}${pkg}|${bin}|package-installed-binary-missing\n"
      fi
    else
      missing="${missing}${pkg}|${bin}|package-unavailable-source-build-required\n"
    fi
  }
  for item in \
    "bash|bash" "zsh|zsh" "fish|fish" "dash|dash" "mksh|mksh" "yash|yash" \
    "elvish|elvish" "nushell|nu" \
    "xterm|xterm" "gnome-terminal|gnome-terminal" "konsole|konsole" \
    "xfce4-terminal|xfce4-terminal" "foot|foot" "kitty|kitty" \
    "alacritty|alacritty" "wezterm|wezterm" "ghostty|ghostty" \
    "contour|contour"; do
    pkg="${item%%|*}"; bin="${item#*|}"
    install_one "$pkg" "$bin"
  done
  mkdir -p /usr/share/chimera/aurora
  printf "%b" "$installed" > /usr/share/chimera/aurora/terminal-shell-installed.tsv
  printf "%b" "$missing" > /usr/share/chimera/aurora/terminal-shell-source-required.tsv
  apt-get clean
  rm -rf /var/lib/apt/lists/*
'
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
install -D -m 0755 "$REPO_DIR/aurora/terminals/aurora-terminal-center.sh" "$ROOTFS/usr/local/bin/aurora-terminal-center"
install -D -m 0755 "$REPO_DIR/aurora/shells/aurora-shell-center.sh" "$ROOTFS/usr/local/bin/aurora-shell-center"
printf 'Terminal/shell package acquisition completed; inspect target manifest for source-build-required entries.\n'
