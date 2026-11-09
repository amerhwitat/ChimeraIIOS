#!/usr/bin/env bash
set -euo pipefail
usage() {
  cat <<'HELP'
Chimera / Octavian IDE manager
Usage: bash tools/ides/ide-manager.sh list
       bash tools/ides/ide-manager.sh install vscodium
       bash tools/ides/ide-manager.sh verify
       bash tools/ides/ide-manager.sh --help
HELP
}
if [ "$#" -eq 0 ]; then cmd="--help"; else cmd="$1"; fi
case "$cmd" in
  --help|-h|help) usage ;;
  list)
    printf '%s\n' 'vscodium - VSCodium (open-source VS Code distribution)' \
      'qt-creator - Qt Creator (open-source/commercial dual licensing)' \
      'geany - Geany (GPL-2.0-or-later)' \
      'codeblocks - Code::Blocks (GPL-3.0-or-later)'
    ;;
  verify)
    if command -v codium >/dev/null 2>&1; then codium --version
    elif command -v vscodium >/dev/null 2>&1; then vscodium --version
    elif command -v code-oss >/dev/null 2>&1; then code-oss --version
    else echo "No supported open-source VS Code executable found." >&2; exit 1
    fi
    ;;
  install)
    if [ "$#" -lt 2 ] || [ "$2" != "vscodium" ]; then
      echo "Only the reviewed vscodium package is currently installable." >&2; exit 64
    fi
    if command -v flatpak >/dev/null 2>&1; then
      flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
      exec flatpak --user install flathub com.vscodium.codium
    elif command -v winget >/dev/null 2>&1; then
      exec winget install --id VSCodium.VSCodium --exact --accept-package-agreements --accept-source-agreements
    elif command -v brew >/dev/null 2>&1; then
      exec brew install --cask vscodium
    else
      echo "Install Flatpak (Linux), winget (Windows), or Homebrew (macOS), then retry." >&2
      exit 69
    fi
    ;;
  *) usage >&2; exit 64 ;;
esac
