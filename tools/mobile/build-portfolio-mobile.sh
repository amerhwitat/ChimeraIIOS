#!/usr/bin/env bash

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -euo pipefail
ROOT="${1:-$HOME/chimera-mobile-workspace}"
mkdir -p "$ROOT"
repos=(BizX BizXtreme ChimeraIIOS CPU4096 CPU4096Simulator PDFreaderPY nlp eth-key-check bruteforce keygen test general VanG)
command -v git >/dev/null || { echo 'git is required'; exit 2; }
for repo in "${repos[@]}"; do
  dir="$ROOT/$repo"
  if [[ -d "$dir/.git" ]]; then git -C "$dir" pull --ff-only; else git clone "https://github.com/amerhwitat/$repo.git" "$dir"; fi
  while IFS= read -r settings; do
    mobile="$(dirname "$settings")"; (cd "$mobile"; if [[ -x ./gradlew ]]; then ./gradlew clean assembleDebug assembleRelease; else gradle clean assembleDebug assembleRelease; fi)
  done < <(find "$dir" -name settings.gradle.kts -type f -print)
done
echo 'Portfolio mobile APK build completed.'
