#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/kali/import-kali-source.sh

Usage:
  tools/kali/import-kali-source.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
DEST=${1:-third_party/kali}
PKG=${2:-}
[ -n "$PKG" ] || { echo "usage: import-kali-source.sh DEST PACKAGE" >&2; exit 2; }
command -v apt-cache >/dev/null 2>&1 || { echo "apt-cache required" >&2; exit 3; }
mkdir -p "$DEST"
echo "Kali source import is package-scoped. Obtain the Debian source package through the configured repository, inspect debian/copyright, then rebuild it for Chimera."
echo "No binary or source package is copied automatically and no non-free package is imported without license approval."
echo "Requested package: $PKG"
