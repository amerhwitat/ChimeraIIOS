#!/bin/sh
set -eu
if command -v x-terminal-emulator >/dev/null 2>&1; then
  exec x-terminal-emulator -e /usr/bin/chimera-ai-workspace chat
elif command -v xterm >/dev/null 2>&1; then
  exec xterm -e /usr/bin/chimera-ai-workspace chat
elif command -v gnome-terminal >/dev/null 2>&1; then
  exec gnome-terminal -- /usr/bin/chimera-ai-workspace chat
fi
exec /usr/bin/chimera-ai-workspace chat
