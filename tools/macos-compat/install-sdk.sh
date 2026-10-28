#!/usr/bin/env bash
# Install/verify Apple's SDK using Apple's own installer on a compatible Mac.
# This script never downloads, copies, or redistributes Apple SDK files.
set -euo pipefail
mode="${1:-check}"
host="$(uname -s)"
if [[ "$host" != "Darwin" ]]; then
  echo "ERROR: Apple's macOS SDK can only be installed/used on Apple-branded hardware running macOS." >&2
  echo "Use the portable-gnustep profile on Linux; it is not the Apple SDK." >&2
  exit 2
fi
case "$mode" in check|install) ;; *) echo "Usage: $0 [check|install]" >&2; exit 64 ;; esac
sdk_ready() {
  command -v xcrun >/dev/null 2>&1 || return 1
  local sdk
  sdk="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null)" || return 1
  [[ -d "$sdk" && -f "$sdk/SDKSettings.plist" ]] || return 1
  command -v clang >/dev/null 2>&1 || return 1
  printf 'APPLE_MACOS_SDK_READY=1\nSDKROOT=%s\n' "$sdk"
  clang --version | head -n 1
}
if sdk_ready; then exit 0; fi
if [[ "$mode" == "check" ]]; then
  echo "ERROR: macOS SDK/Clang toolchain is not installed or selected." >&2
  echo "Run: bash tools/macos-compat/install-sdk.sh install" >&2
  exit 3
fi
if ! command -v xcode-select >/dev/null 2>&1; then
  echo "ERROR: xcode-select is missing; install Xcode or Command Line Tools from Apple." >&2
  exit 4
fi
echo "Requesting Apple's interactive Command Line Tools installer..."
if xcode-select --install; then
  echo "INSTALL_REQUESTED=1"
else
  rc=$?
  echo "INFO: xcode-select --install returned $rc; an installer may already be pending or full Xcode may be installed." >&2
fi
echo "Complete the Apple installer/license prompts, then rerun this command to verify the SDK." >&2
echo "For full Xcode installs, select Xcode in Xcode > Settings > Locations or run xcode-select --switch with the installed Developer directory." >&2
exit 10
