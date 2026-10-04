#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: mobile/ios/build-mobile.sh

Usage:
  mobile/ios/build-mobile.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
[[ "$(uname -s)" == "Darwin" ]] || { echo "[Chimera][ERROR] iOS builds require macOS/Xcode." >&2; exit 2; }
command -v xcodebuild >/dev/null || { echo "[Chimera][ERROR] xcodebuild not found." >&2; exit 2; }
echo "[Chimera] Apple mobile build contract validated."
