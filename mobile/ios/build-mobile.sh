#!/usr/bin/env bash
set -euo pipefail
[[ "$(uname -s)" == "Darwin" ]] || { echo "[Chimera][ERROR] iOS builds require macOS/Xcode." >&2; exit 2; }
command -v xcodebuild >/dev/null || { echo "[Chimera][ERROR] xcodebuild not found." >&2; exit 2; }
echo "[Chimera] Apple mobile build contract validated."
