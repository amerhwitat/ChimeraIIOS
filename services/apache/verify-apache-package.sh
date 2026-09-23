#!/usr/bin/env bash
set -euo pipefail

PKG="${1:?package directory required}"

test -d "$PKG" || { echo "ERROR: package directory missing: $PKG"; exit 1; }
test -f "$PKG/SHA256" || { echo "ERROR: SHA256 record missing"; exit 1; }
test -f "$PKG/ARTIFACT" || { echo "ERROR: ARTIFACT record missing"; exit 1; }
test -f "$PKG/SIGNATURE" || { echo "ERROR: detached signature missing"; exit 1; }
test -f "$PKG/PROVENANCE.json" || { echo "ERROR: provenance record missing"; exit 1; }
test -d "$PKG/payload" || { echo "ERROR: unpacked payload missing"; exit 1; }

if command -v gpg >/dev/null 2>&1; then
    artifact="$(cat "$PKG/ARTIFACT")"
    test -f "$artifact" || { echo "ERROR: cached artifact missing: $artifact"; exit 1; }
    gpg --batch --verify "$PKG/SIGNATURE" "$artifact"
else
    echo "ERROR: gpg is required for Apache release verification" >&2
    exit 1
fi

license_path="$PKG/$(cat "$PKG/LICENSE-PATH")"
notice_path="$PKG/$(cat "$PKG/NOTICE-PATH")"
test -f "$license_path" || { echo "ERROR: LICENSE missing: $license_path"; exit 1; }
test -f "$notice_path" || { echo "ERROR: NOTICE missing: $notice_path"; exit 1; }

echo "Apache package verified: $PKG"
