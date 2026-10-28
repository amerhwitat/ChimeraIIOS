#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <apple-macos|portable-gnustep> <source.m|source.mm|source.c|source.cpp> <output>" >&2
  exit 64
fi
profile="$1"; source="$2"; output="$3"
case "$profile" in apple-macos|portable-gnustep) ;; *) echo "ERROR: unknown profile." >&2; exit 64 ;; esac
[[ -f "$source" ]] || { echo "ERROR: source file not found: $source" >&2; exit 66; }
mkdir -p "$(dirname "$output")"
case "$profile" in
  apple-macos)
    [[ "$(uname -s)" == "Darwin" ]] || { echo "ERROR: Apple macOS SDK builds must run on Apple-branded macOS hardware." >&2; exit 2; }
    sdk="$(xcrun --sdk macosx --show-sdk-path)"
    [[ -f "$sdk/SDKSettings.plist" ]] || { echo "ERROR: macOS SDK not found; install Xcode Command Line Tools." >&2; exit 3; }
    case "$source" in
      *.m|*.mm) clang -isysroot "$sdk" -mmacosx-version-min="${MACOSX_DEPLOYMENT_TARGET:-12.0}" "$source" -o "$output" ;;
      *.c|*.cpp) clang -isysroot "$sdk" -mmacosx-version-min="${MACOSX_DEPLOYMENT_TARGET:-12.0}" "$source" -o "$output" ;;
      *) echo "ERROR: unsupported source extension: $source" >&2; exit 65 ;;
    esac
    ;;
  portable-gnustep)
    command -v clang >/dev/null || { echo "ERROR: clang not found." >&2; exit 4; }
    command -v gnustep-config >/dev/null || { echo "ERROR: GNUstep is required for Foundation-style portable apps. Install GNUstep Base development packages for this host." >&2; exit 5; }
    case "$source" in
      *.m|*.mm) # GNUstep flags are intentionally evaluated as shell words from the trusted local tool.
        # shellcheck disable=SC2046
        clang $(gnustep-config --objc-flags) "$source" -o "$output" $(gnustep-config --base-libs)
        ;;
      *.c|*.cpp) clang "$source" -o "$output" ;;
      *) echo "ERROR: unsupported source extension: $source" >&2; exit 65 ;;
    esac
    ;;
  *) echo "ERROR: unknown profile '$profile'." >&2; exit 64 ;;
esac
printf 'BUILD_PROFILE=%s\nOUTPUT=%s\n' "$profile" "$output"
