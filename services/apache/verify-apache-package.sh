#!/usr/bin/env bash
set -euo pipefail
PKG="${1:?package directory required}"
test -f "$PKG/LICENSE" || { echo "ERROR: LICENSE missing"; exit 1; }
test -f "$PKG/NOTICE" || { echo "ERROR: NOTICE missing"; exit 1; }
test -f "$PKG/SHA256" || { echo "ERROR: SHA256 record missing"; exit 1; }
if command -v gpg >/dev/null && test -f "$PKG/SIGNATURE"; then gpg --verify "$PKG/SIGNATURE" "$PKG/ARTIFACT"; fi
echo "Apache package verification metadata present: $PKG"
