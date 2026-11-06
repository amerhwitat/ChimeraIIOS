#!/usr/bin/env bash
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'HELP'
Usage: aurora/terminals/install-desktop-entries.sh
Creates Aurora launchers only for terminal and shell executables present in CHIMERA_ROOTFS_DIR.
HELP
  exit 0
fi
set -Eeuo pipefail
ROOTFS="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR is required}"
APPS="$ROOTFS/usr/share/applications"
mkdir -p "$APPS"
has_binary() {
  local bin="$1"
  [[ -x "$ROOTFS/usr/bin/$bin" || -x "$ROOTFS/bin/$bin" ]]
}
# Do not publish a desktop launcher for a catalogue-only or missing executable.
terminals=(
  "xterm|XTerm|xterm"
  "gnome-terminal|GNOME Terminal|gnome-terminal"
  "gnome-console|GNOME Console|kgx"
  "konsole|Konsole|konsole"
  "xfce4-terminal|XFCE Terminal|xfce4-terminal"
  "foot|Foot|foot"
  "kitty|Kitty|kitty"
  "ptyxis|Ptyxis|ptyxis"
  "alacritty|Alacritty|alacritty"
  "wezterm|WezTerm|wezterm"
  "ghostty|Ghostty|ghostty"
  "contour|Contour|contour"
  "terminator|Terminator|terminator"
  "tilix|Tilix|tilix"
  "mate-terminal|MATE Terminal|mate-terminal"
  "qterminal|QTerminal|qterminal"
  "sakura|Sakura|sakura"
  "terminology|Terminology|terminology"
  "lxterminal|LXTerminal|lxterminal"
  "blackbox-terminal|Black Box Terminal|blackbox"
)
for spec in "${terminals[@]}"; do
  IFS='|' read -r id name bin <<< "$spec"
  if has_binary "$bin"; then
    cat > "$APPS/chimera-terminal-$id.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Comment=Aurora terminal emulator
Exec=$bin
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;Utility;Development;
X-Chimera-Aurora=true
X-Chimera-Terminal-ID=$id
EOF
  else
    rm -f "$APPS/chimera-terminal-$id.desktop"
    printf '[AURORA] no launcher for %s: executable %s is absent\n' "$id" "$bin"
  fi
done
shells=(
  "bash|Bash|bash"
  "zsh|Zsh|zsh"
  "fish|fish|fish"
  "dash|Dash|dash"
  "mksh|mksh|mksh"
  "yash|Yash|yash"
  "elvish|Elvish|elvish"
  "nushell|Nushell|nu"
)
for spec in "${shells[@]}"; do
  IFS='|' read -r id name bin <<< "$spec"
  if has_binary "$bin" && [[ -x "$ROOTFS/usr/lib/chimera/aurora/launch-shell.sh" ]]; then
    cat > "$APPS/chimera-shell-$id.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Aurora Shell — $name
Comment=Launch the $name shell in the selected terminal
Exec=/usr/lib/chimera/aurora/launch-shell.sh $id
Terminal=true
Categories=System;TerminalEmulator;Development;
X-Chimera-Aurora=true
X-Chimera-Shell-ID=$id
EOF
  else
    rm -f "$APPS/chimera-shell-$id.desktop"
    printf '[AURORA] no shell launcher for %s: executable or launcher is absent\n' "$id"
  fi
done
