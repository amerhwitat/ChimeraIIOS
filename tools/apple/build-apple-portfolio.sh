#!/usr/bin/env bash
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
