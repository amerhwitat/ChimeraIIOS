#!/usr/bin/env bash
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
