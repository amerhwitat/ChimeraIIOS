#!/usr/bin/env sh
# Chimera II OS terminal welcome banner. POSIX sh; no external dependencies.
[ "${CHIMERA_NO_COLOR:-0}" = 1 ] && color=0 || color=1
if [ "$color" = 1 ] && [ -t 1 ]; then
  cyan=$(printf '\033[1;36m'); blue=$(printf '\033[0;34m'); reset=$(printf '\033[0m')
else
  cyan=; blue=; reset=
fi
printf '%s' "$cyan"
cat <<'CHIMERA'
   _____ _     ___ __  __ _____ ____      _    ___ ___
  / ____| |   |_ _|  \/  | ____|  _ \    / \  |_ _/ _ \
 | |    | |    | || |\/| |  _| | |_) |  / _ \  | | | |
 | |____| |___ | || |  | | |___|  _ <  / ___ \ | | |_| |
  \_____|_____|___|_|  |_|_____|_| \_\/_/   \_\___\___/
CHIMERA
printf '%s' "$reset"
printf 'Chimera II OS | Aurora Wayland Glass Desktop\n'
printf 'Open shells: bash, zsh, fish, dash, ksh, tcsh, yash, nushell, PowerShell*\n'
printf 'Terminals: Aurora Terminal (native), plus installed compatible emulators\n'
printf 'Type "help" for commands. Optional providers are shown only when installed.\n'
printf '\n'
