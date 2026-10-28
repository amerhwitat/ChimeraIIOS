#!/usr/bin/env bash
set -euo pipefail
mode="${1:-auto}"
host="$(uname -s)"
if [[ "$mode" == "apple-sdk" ]]; then
  if [[ "$host" != "Darwin" ]]; then
    echo "ERROR: Apple macOS SDK use is restricted by its license; run Xcode/macOS SDK tooling on Apple-branded macOS hardware." >&2
    exit 2
  fi
  if ! command -v xcrun >/dev/null 2>&1; then
    echo "ERROR: xcrun not found. Install Xcode Command Line Tools on macOS." >&2
    exit 3
  fi
  sdk="$(xcrun --sdk macosx --show-sdk-path)"
  [[ -d "$sdk" && -f "$sdk/SDKSettings.plist" ]] || { echo "ERROR: macOS SDK path is invalid: $sdk" >&2; exit 4; }
  command -v clang >/dev/null
  printf 'APPLE_MACOS_SDK_READY=1\nSDKROOT=%s\n' "$sdk"
  exit 0
fi
if [[ "$mode" == "portable" ]]; then
  command -v clang >/dev/null || { echo "ERROR: clang is required for portable Objective-C/C/C++ builds." >&2; exit 5; }
  if command -v gnustep-config >/dev/null 2>&1; then
    echo "PORTABLE_OBJC_RUNTIME=gnustep"
  else
    echo "PORTABLE_OBJC_RUNTIME=unavailable"
    echo "NOTE: Install GNUstep Base development packages to build Foundation-style portable apps."
  fi
  echo "PORTABLE_TOOLCHAIN_READY=1"
  exit 0
fi
if [[ "$host" == "Darwin" ]]; then exec "$0" apple-sdk; fi
exec "$0" portable
