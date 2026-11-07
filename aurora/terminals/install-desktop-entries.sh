#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: aurora/terminals/install-desktop-entries.sh

Usage:
  aurora/terminals/install-desktop-entries.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOTFS="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR is required}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
APPS="$ROOTFS/usr/share/applications"
MANIFEST_DIR="$ROOTFS/usr/share/chimera/aurora"
mkdir -p "$APPS" "$MANIFEST_DIR"
TERMINAL_MANIFEST="$MANIFEST_DIR/terminal-shell-installed.tsv"
SHELL_MANIFEST="$MANIFEST_DIR/shells-installed.tsv"
: > "$SHELL_MANIFEST"
cat > "$APPS/chimera-terminal-center.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Aurora Terminal Center
Comment=Chimera II OS terminal emulator and shell launcher
Exec=aurora-terminal-center
Terminal=true
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Panel=Terminals & Shells
EOF
cat > "$APPS/chimera-shell-center.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Aurora Shell Center
Comment=Choose an installed open-source command shell
Exec=aurora-shell-center
Terminal=true
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Panel=Terminals & Shells
EOF
for spec in \
  'xterm|XTerm|xterm' \
  'gnome-terminal|GNOME Terminal|gnome-terminal' \
  'gnome-console|GNOME Console|kgx' \
  'konsole|Konsole|konsole' \
  'xfce4-terminal|XFCE Terminal|xfce4-terminal' \
  'foot|Foot|foot' \
  'kitty|Kitty|kitty' \
  'ptyxis|Ptyxis|ptyxis' \
  'alacritty|Alacritty|alacritty' \
  'wezterm|WezTerm|wezterm' \
  'ghostty|Ghostty|ghostty' \
  'contour|Contour|contour' \
  'terminator|Terminator|terminator' \
  'tilix|Tilix|tilix' \
  'mate-terminal|MATE Terminal|mate-terminal' \
  'qterminal|QTerminal|qterminal' \
  'sakura|Sakura|sakura' \
  'terminology|Terminology|terminology' \
  'lxterminal|LXTerminal|lxterminal' \
  'blackbox-terminal|Black Box Terminal|blackbox'; do
  IFS='|' read -r id name bin <<< "$spec"
  if ! chroot "$ROOTFS" /bin/sh -c "command -v '$bin' >/dev/null 2>&1"; then
    printf '[Aurora] Not exposing %s: executable %s is not installed.\\n' "$id" "$bin" >&2
    continue
  fi
  if ! awk -F'|' -v b="$bin" '$2 == b { found=1 } END { exit !found }' "$TERMINAL_MANIFEST"; then
    printf '%s|%s\\n' "$id" "$bin" >> "$TERMINAL_MANIFEST"
  fi
  cat > "$APPS/chimera-terminal-$id.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Comment=Aurora terminal emulator
Exec=$bin
Terminal=false
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Terminal-ID=$id
EOF
done

# Record installed shell providers and install the two Aurora selector commands.
for spec in \
  'bash|GNU Bash|bash' \
  'zsh|Z Shell|zsh' \
  'fish|fish|fish' \
  'dash|Debian Almquist Shell|dash' \
  'mksh|MirBSD Korn Shell|mksh' \
  'yash|Yet Another Shell|yash' \
  'elvish|Elvish|elvish' \
  'nushell|Nushell|nu'; do
  IFS='|' read -r id name bin <<< "$spec"
  if chroot "$ROOTFS" /bin/sh -c "command -v '$bin' >/dev/null 2>&1"; then
    printf '%s|%s\\n' "$id" "$bin" >> "$SHELL_MANIFEST"
  else
    printf '[Aurora] Shell provider not installed: %s (%s)\\n' "$id" "$bin" >&2
  fi
done
install -D -m 0755 "$SCRIPT_DIR/aurora-terminal-center.sh" "$ROOTFS/usr/local/bin/aurora-terminal-center"
install -D -m 0755 "$REPO_ROOT/aurora/shells/launch-shell.sh" "$ROOTFS/usr/local/bin/aurora-shell-center"
