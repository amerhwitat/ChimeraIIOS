#!/usr/bin/env bash
set -Eeuo pipefail
ROOTFS="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR is required}"
APPS="$ROOTFS/usr/share/applications"
mkdir -p "$APPS"
cat > "$APPS/chimera-terminal-center.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Aurora Terminal Center
Comment=Chimera II OS terminal emulator and shell launcher
Exec=aurora-terminal-center
Terminal=false
Categories=System;TerminalEmulator;
X-Chimera-Aurora=true
X-Chimera-Panel=Terminals & Shells
EOF
for spec in \
  'xterm|XTerm|xterm' \
  'gnome-terminal|GNOME Terminal|gnome-terminal' \
  'konsole|Konsole|konsole' \
  'xfce4-terminal|XFCE Terminal|xfce4-terminal' \
  'foot|Foot|foot' \
  'kitty|Kitty|kitty' \
  'alacritty|Alacritty|alacritty' \
  'wezterm|WezTerm|wezterm' \
  'ghostty|Ghostty|ghostty' \
  'contour|Contour|contour'; do
  IFS='|' read -r id name bin <<< "$spec"
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
