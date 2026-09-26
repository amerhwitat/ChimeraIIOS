#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/tools/branding/stage-aurora-image.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

bash -n "$SCRIPT"
command -v python3 >/dev/null 2>&1 || { echo "SKIP: python3 is not installed"; exit 0; }
command -v base64 >/dev/null 2>&1 || { echo "SKIP: base64 is not installed"; exit 0; }

# Reproduce the failure class: a valid PNG base64 payload plus one stray
# base64-alphabet character gives a length of 1 modulo 4.
python3 - "$TMP/good.b64" "$TMP/bad.b64" <<'PY'
import base64, pathlib
png = b'\x89PNG\r\n\x1a\n' + b'CHIMERA-AURORA-TEST'
encoded = base64.b64encode(png)
pathlib.Path(__import__('sys').argv[1]).write_bytes(encoded)
pathlib.Path(__import__('sys').argv[2]).write_bytes(encoded + b'A')
PY

# Extract the decoder function without executing the staging side effects.
awk '/^decode_embedded\(\)/,/^normalize_to_png\(\)/ { if ($0 !~ /^normalize_to_png/) print }' "$SCRIPT" > "$TMP/decoder.sh"
# shellcheck disable=SC1090
source "$TMP/decoder.sh"
decode_embedded "$TMP/bad.b64" "$TMP/recovered.png" "89504e470d0a1a0a"
test "$(od -An -tx1 -N8 "$TMP/recovered.png" | tr -d ' \n')" = "89504e470d0a1a0a"

echo "PASS: Aurora base64 one-character recovery"
