#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${1:?usage: install-terminal-shell-suite.sh ROOTFS}"
[[ -d "$ROOTFS" && -x "$ROOTFS/bin/sh" ]] || { echo "invalid target rootfs: $ROOTFS" >&2; exit 2; }
chroot "$ROOTFS" /bin/sh -eu -c '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y --no-install-recommends binutils
  target_arch="$(dpkg --print-architecture)"
  case "$target_arch" in
    amd64) expected_machine="Advanced Micro Devices X86-64" ;;
    arm64) expected_machine="AArch64" ;;
    armel|armhf) expected_machine="ARM" ;;
    i386) expected_machine="Intel 80386" ;;
    riscv64) expected_machine="RISC-V" ;;
    ppc64el) expected_machine="PowerPC64" ;;
    s390x) expected_machine="IBM S/390" ;;
    *) echo "Unsupported target dpkg architecture: $target_arch" >&2; exit 2 ;;
  esac
  installed=""
  missing=""
  install_one() {
    pkg="$1"; bin="$2"
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      if ! apt-get install -y --no-install-recommends "$pkg"; then
        missing="${missing}${pkg}|${bin}|package-install-failed-source-build-required\n"
        return 0
      fi
      if command -v "$bin" >/dev/null 2>&1; then
        binary_path="$(command -v "$bin")"
        if readelf -h "$binary_path" >/tmp/chimera-terminal-elf 2>/dev/null; then
          machine="$(sed -n "/Machine:/s/.*Machine: *//p" /tmp/chimera-terminal-elf)"
          rm -f /tmp/chimera-terminal-elf
          if [ -z "$machine" ] || [ "$machine" != "$expected_machine" ]; then
            missing="${missing}${pkg}|${bin}|package-elf-machine-mismatch-source-build-required:${machine}\\n"
          else
            installed="${installed}${pkg}|${bin}|${machine}\\n"
          fi
        else
          rm -f /tmp/chimera-terminal-elf
          first_line="$(head -n 1 "$binary_path" 2>/dev/null || true)"
          interpreter="$(printf "%s" "$first_line" | sed -n "s/^#!\\([^ ]*\\).*/\\1/p")"
          if [ -n "$interpreter" ] && [ -x "$interpreter" ]; then
            installed="${installed}${pkg}|${bin}|script-provider:${interpreter}\\n"
          else
            missing="${missing}${pkg}|${bin}|package-script-interpreter-missing-source-build-required\\n"
          fi
        fi
      else
        missing="${missing}${pkg}|${bin}|package-installed-binary-missing\\n"
      fi
    else
      missing="${missing}${pkg}|${bin}|package-unavailable-source-build-required\n"
    fi
  }
  for item in \
    "bash|bash" "zsh|zsh" "fish|fish" "dash|dash" "mksh|mksh" "yash|yash" \
    "elvish|elvish" "nushell|nu" \
    "xterm|xterm" "gnome-terminal|gnome-terminal" "gnome-console|kgx" "konsole|konsole" \
    "xfce4-terminal|xfce4-terminal" "foot|foot" "kitty|kitty" "ptyxis|ptyxis" \
    "alacritty|alacritty" "wezterm|wezterm" "ghostty|ghostty" "contour|contour" \
    "terminator|terminator" "tilix|tilix" "mate-terminal|mate-terminal" "qterminal|qterminal" \
    "sakura|sakura" "terminology|terminology" "lxterminal|lxterminal" "blackbox-terminal|blackbox"; do
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
ln -sfn /usr/local/bin/aurora-terminal-center "$ROOTFS/usr/local/bin/chimera-terminal"
ln -sfn /usr/local/bin/aurora-terminal-center "$ROOTFS/usr/local/bin/chimera-terminals"
ln -sfn /usr/local/bin/aurora-shell-center "$ROOTFS/usr/local/bin/chimera-shell-ar"
printf 'Terminal/shell package acquisition completed; inspect target manifest for source-build-required entries.\n'
