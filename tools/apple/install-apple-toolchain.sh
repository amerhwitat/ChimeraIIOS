#!/usr/bin/env bash
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
