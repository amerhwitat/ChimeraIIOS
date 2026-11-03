#!/usr/bin/env bash
set -euo pipefail
candidates=(
  "${CHIMERA_VOICECONNECT_BIN:-}"
  /opt/voiceconnect/VoiceConnect
  /opt/voiceconnect/voiceconnect
  /usr/local/bin/voiceconnect
  /usr/bin/voiceconnect
)
for candidate in "${candidates[@]}"; do
  [[ -n "$candidate" && -x "$candidate" ]] || continue
  exec "$candidate" "$@"
done
url="${CHIMERA_VOICECONNECT_URL:-https://github.com/amerhwitat/test/tree/feat/voiceconnect-p2p-camera}"
if command -v xdg-open >/dev/null 2>&1; then
  exec xdg-open "$url"
fi
printf '[Aurora] VoiceConnect is not installed. Obtain a verified package from %s\n' "$url" >&2
exit 127
