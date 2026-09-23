#!/usr/bin/env bash
set -euo pipefail

PREFIX="${CHIMERA_APACHE_PREFIX:-/opt/chimera/apache}"
CACHE="${CHIMERA_APACHE_CACHE:-/var/cache/chimera/apache}"
CATALOG_URL="${CHIMERA_APACHE_PROJECT_INDEX:-https://projects.apache.org/json/projects/}"
RELEASE_URL="${CHIMERA_APACHE_RELEASE_INDEX:-https://downloads.apache.org/}"
REGISTRY="${PREFIX}/registry"
SYNC="${CHIMERA_APACHE_SYNC:-/usr/bin/apache-sync.py}"

mkdir -p "$PREFIX" "$CACHE" "$REGISTRY"

command -v curl >/dev/null || { echo "ERROR: curl required"; exit 1; }
command -v sha256sum >/dev/null || { echo "ERROR: sha256sum required"; exit 1; }

export CHIMERA_APACHE_PREFIX="$PREFIX"
export CHIMERA_APACHE_CACHE="$CACHE"
export CHIMERA_APACHE_PROJECT_INDEX="$CATALOG_URL"
export CHIMERA_APACHE_RELEASE_INDEX="$RELEASE_URL"

if [ -x "$SYNC" ] || command -v "$SYNC" >/dev/null 2>&1; then
    "$SYNC" catalog
else
    command -v python3 >/dev/null || { echo "ERROR: python3 required"; exit 1; }
    python3 "$PREFIX/apache-sync.py" catalog
fi

date -u +%FT%TZ > "$REGISTRY/catalog-refreshed-at"
cat > "$REGISTRY/README" <<'EOF'
Apache ecosystem package registry for Chimera II OS.

The registry tracks the complete ASF project catalog. Installation is restricted
to official ASF release artifacts from downloads.apache.org. Release candidates,
nightlies, snapshots, /dev artifacts and unapproved builds are rejected.

Every installed package records SHA-256 provenance, detached-signature
verification status, and LICENSE/NOTICE locations.
EOF

cat > "$REGISTRY/SOURCES" <<EOF
PROJECT_CATALOG=$CATALOG_URL
RELEASE_DISTRIBUTION=$RELEASE_URL
ARTIFACT_POLICY=official-releases-only
SIGNATURE_REQUIRED=1
LICENSE_REQUIRED=1
NOTICE_REQUIRED=1
EOF

echo "[INFO] Apache project catalog refreshed."
echo "[INFO] Official ASF release resolver is ready."
