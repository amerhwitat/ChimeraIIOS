#!/usr/bin/env bash
set -euo pipefail
ROOT="${CHIMERA_TERMINAL_ROOT:-/opt/chimera}"
CATALOG="${CHIMERA_TERMINAL_CATALOG:-/build/repos/ChimeraIIOS/system/terminals/chimera-terminals.json}"
APP_DIR="/usr/share/applications"
META_DIR="$ROOT/share/chimera/terminals"
mkdir -p "$META_DIR" "$APP_DIR"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -o Acquire::Retries=5
  candidates=()
  for p in foot alacritty kitty wezterm ptyxis gnome-terminal gnome-console konsole xfce4-terminal terminator tilix mate-terminal qterminal sakura terminology lxterminal blackbox-terminal xterm; do
    if apt-cache policy "$p" 2>/dev/null | grep -q 'Candidate:'; then candidates+=("$p"); else echo "[Chimera][TERMINALS] package unavailable: $p"; fi
  done
  for p in "${candidates[@]}"; do
    apt-get install -y --no-install-recommends "$p" || echo "[Chimera][TERMINALS][WARN] skipped package: $p"
  done
  rm -rf /var/lib/apt/lists/*
fi
[ -f "$CATALOG" ] && install -m 0644 "$CATALOG" "$META_DIR/chimera-terminals.json"
desktop_for() {
  local id="$1" bin="$2" en="$3" ar="$4"
  command -v "$bin" >/dev/null 2>&1 || return 0
  cat > "$APP_DIR/chimera-$id.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Chimera: $en
Name[ar]=$ar
Comment=Chimera II OS terminal emulator
Comment[ar]=محاكي طرفية في نظام شيميرا II
Exec=$bin
Icon=utilities-terminal
Terminal=false
Categories=System;TerminalEmulator;Utility;Development;
Keywords=terminal;shell;chimera;wayland;طرفية;شيميرا;
StartupNotify=true
EOF
}
desktop_for foot foot "Foot Terminal" "طرفية Foot"
desktop_for alacritty alacritty "Alacritty Terminal" "طرفية Alacritty"
desktop_for kitty kitty "Kitty Terminal" "طرفية Kitty"
desktop_for wezterm wezterm "WezTerm" "طرفية WezTerm"
desktop_for ptyxis ptyxis "Ptyxis Terminal" "طرفية Ptyxis"
desktop_for gnome-terminal gnome-terminal "GNOME Terminal" "طرفية GNOME"
desktop_for gnome-console kgx "GNOME Console" "طرفية GNOME Console"
desktop_for konsole konsole "Konsole Terminal" "طرفية Konsole"
desktop_for xfce4-terminal xfce4-terminal "XFCE Terminal" "طرفية XFCE"
desktop_for terminator terminator "Terminator" "طرفية Terminator"
desktop_for tilix tilix "Tilix Terminal" "طرفية Tilix"
desktop_for mate-terminal mate-terminal "MATE Terminal" "طرفية MATE"
desktop_for qterminal qterminal "QTerminal" "طرفية QTerminal"
desktop_for sakura sakura "Sakura Terminal" "طرفية Sakura"
desktop_for terminology terminology "Terminology" "طرفية Terminology"
desktop_for lxterminal lxterminal "LXTerminal" "طرفية LX"
desktop_for blackbox-terminal blackbox "Black Box Terminal" "طرفية Black Box"
desktop_for xterm xterm "XTerm" "طرفية XTerm"
