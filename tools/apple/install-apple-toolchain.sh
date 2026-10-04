#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/apple/install-apple-toolchain.sh

Usage:
  tools/apple/install-apple-toolchain.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then echo "Apple iOS/macOS compilation requires macOS with Xcode." >&2; exit 2; fi
command -v xcodebuild >/dev/null || { echo "Install Xcode from Apple before continuing." >&2; exit 2; }
command -v xcrun >/dev/null || { echo "Xcode Command Line Tools are required." >&2; exit 2; }
command -v swift >/dev/null || { echo "Swift/Xcode toolchain not found." >&2; exit 2; }
xcodebuild -version
xcrun --sdk iphoneos --show-sdk-path
xcrun --sdk macosx --show-sdk-path
if command -v brew >/dev/null 2>&1; then
  brew install ruby bundler xcodegen 2>/dev/null || true
fi
if command -v fastlane >/dev/null 2>&1; then fastlane --version; else echo "fastlane optional: gem install fastlane --no-document"; fi
if command -v xcodegen >/dev/null 2>&1; then xcodegen --version; else echo "xcodegen optional: brew install xcodegen"; fi
echo "Apple toolchain prerequisites are available."
