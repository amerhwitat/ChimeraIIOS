#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: apple/scripts/export-ipa.sh

Usage:
  apple/scripts/export-ipa.sh [options] [arguments]

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
: "${SCHEME:?Set SCHEME}"
ARCHIVE="${ARCHIVE:-build/archive/${SCHEME}.xcarchive}"
EXPORT_OPTIONS="${EXPORT_OPTIONS:-apple/Config/ExportOptions.plist}"
mkdir -p build/ipa
[[ -d "$ARCHIVE" ]] || { echo "Archive not found: $ARCHIVE" >&2; exit 2; }
[[ -f "$EXPORT_OPTIONS" ]] || { echo "Export options not found: $EXPORT_OPTIONS" >&2; exit 2; }
xcodebuild -exportArchive -archivePath "$ARCHIVE" -exportOptionsPlist "$EXPORT_OPTIONS" -exportPath build/ipa
