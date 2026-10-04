#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/apple/build-apple-portfolio.sh

Usage:
  tools/apple/build-apple-portfolio.sh [options] [arguments]

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
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIGURATION="${CONFIGURATION:-Release}"
SKIP_SIGNING="${SKIP_SIGNING:-1}"
REPOS="${REPOS:-BizX BizXtreme ChimeraIIOS CPU4096 CPU4096Simulator PDFreaderPY nlp eth-key-check bruteforce keygen test general VanG}"

"$ROOT/tools/apple/install-apple-toolchain.sh"

for repo in $REPOS; do
  dir="$ROOT/../$repo"
  [[ -d "$dir" ]] || { echo "Skip $repo: not present at $dir"; continue; }
  while IFS= read -r package; do
    [[ -n "$package" ]] || continue
    echo "Validating Swift package: $package"
    (cd "$package" && swift package dump-package >/dev/null)
  done < <(find "$dir" -name Package.swift -type f -not -path '*/.git/*')

  while IFS= read -r project; do
    [[ -n "$project" ]] || continue
    echo "Apple project discovered: $project"
    echo "Use the repository's documented scheme/archive script for a signed product."
  done < <(find "$dir/apple" -maxdepth 3 \( -name '*.xcodeproj' -o -name '*.xcworkspace' \) -print 2>/dev/null || true)
done

echo "Portfolio Apple source validation complete."
echo "For IPA export on macOS, set PROJECT/WORKSPACE and SCHEME and run apple/scripts/archive-ios.sh then export-ipa.sh."
