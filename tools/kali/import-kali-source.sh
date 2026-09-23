#!/bin/sh
set -eu
DEST=${1:-third_party/kali}
PKG=${2:-}
[ -n "$PKG" ] || { echo "usage: import-kali-source.sh DEST PACKAGE" >&2; exit 2; }
command -v apt-cache >/dev/null 2>&1 || { echo "apt-cache required" >&2; exit 3; }
mkdir -p "$DEST"
echo "Kali source import is package-scoped. Obtain the Debian source package through the configured repository, inspect debian/copyright, then rebuild it for Chimera."
echo "No binary or source package is copied automatically and no non-free package is imported without license approval."
echo "Requested package: $PKG"
