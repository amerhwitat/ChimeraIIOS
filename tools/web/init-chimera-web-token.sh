#!/usr/bin/env bash
set -euo pipefail
TOKEN_FILE="${CHIMERA_WEB_TOKEN_FILE:-/etc/chimera/web.token}"
install -d -m 0700 "$(dirname "$TOKEN_FILE")"
if [[ -s "$TOKEN_FILE" && "${CHIMERA_WEB_FORCE_TOKEN:-0}" != "1" ]]; then
  echo "Existing token retained: $TOKEN_FILE"
  exit 0
fi
umask 077
python3 - <<'PY' > "$TOKEN_FILE"
import secrets
print(secrets.token_urlsafe(48))
PY
chmod 0600 "$TOKEN_FILE"
echo "Created Chimera web console token: $TOKEN_FILE"
