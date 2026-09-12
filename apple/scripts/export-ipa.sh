#!/usr/bin/env bash
set -euo pipefail
: "${SCHEME:?Set SCHEME}"
ARCHIVE="${ARCHIVE:-build/archive/${SCHEME}.xcarchive}"
EXPORT_OPTIONS="${EXPORT_OPTIONS:-apple/Config/ExportOptions.plist}"
mkdir -p build/ipa
[[ -d "$ARCHIVE" ]] || { echo "Archive not found: $ARCHIVE" >&2; exit 2; }
[[ -f "$EXPORT_OPTIONS" ]] || { echo "Export options not found: $EXPORT_OPTIONS" >&2; exit 2; }
xcodebuild -exportArchive -archivePath "$ARCHIVE" -exportOptionsPlist "$EXPORT_OPTIONS" -exportPath build/ipa
