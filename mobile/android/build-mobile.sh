#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: mobile/android/build-mobile.sh

Usage:
  mobile/android/build-mobile.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "\${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="\${CHIMERA_MOBILE_OUT:-\${ROOT}/build/mobile/android}"
mkdir -p "\${OUT}"
if [[ -z "\${ANDROID_HOME:-}" && -z "\${ANDROID_SDK_ROOT:-}" ]]; then
  echo "[Chimera][ERROR] ANDROID_HOME or ANDROID_SDK_ROOT is required." >&2; exit 2
fi
SDK="\${ANDROID_SDK_ROOT:-\${ANDROID_HOME}}"
[[ -x "\${SDK}/platform-tools/adb" ]] || { echo "[Chimera][ERROR] adb not found." >&2; exit 2; }
if [[ ! -x "\${ROOT}/mobile/android/gradlew" ]]; then
  echo "[Chimera][ERROR] Gradle wrapper missing. Generate the wrapper with a pinned Gradle version before packaging." >&2; exit 2
fi
cd "\${ROOT}/mobile/android"
./gradlew --no-daemon assembleDebug
cp -f app/build/outputs/apk/debug/*.apk "\${OUT}/" 2>/dev/null || true
echo "Android mobile build staged in \${OUT}"
