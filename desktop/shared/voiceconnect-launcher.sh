#!/usr/bin/env bash
set -euo pipefail
for candidate in /opt/voiceconnect/VoiceConnect /opt/voiceconnect/voiceconnect /usr/bin/voiceconnect /usr/local/bin/voiceconnect; do
  if [[ -x "$candidate" ]]; then exec "$candidate" "$@"; fi
done
if command -v voiceconnect >/dev/null 2>&1; then exec voiceconnect "$@"; fi
if command -v notify-send >/dev/null 2>&1; then
  notify-send "VoiceConnect is not installed" "Opening the VoiceConnect project. A verified packaged build is required for native launch."
fi
exec xdg-open "https://github.com/amerhwitat/test/tree/feat/voiceconnect-p2p-camera"
