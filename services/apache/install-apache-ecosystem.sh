#!/usr/bin/env bash
set -euo pipefail
PREFIX="${CHIMERA_APACHE_PREFIX:-/opt/chimera/apache}"
CACHE="${CHIMERA_APACHE_CACHE:-/var/cache/chimera/apache}"
CATALOG="${CHIMERA_APACHE_CATALOG:-https://projects.apache.org/json/projects/}"
REGISTRY="${PREFIX}/registry"
mkdir -p "$PREFIX" "$CACHE" "$REGISTRY"
command -v curl >/dev/null || { echo "curl required"; exit 1; }
command -v sha256sum >/dev/null || { echo "sha256sum required"; exit 1; }
curl -fsSL "$CATALOG" -o "$CACHE/projects-index.html"
date -u +%FT%TZ > "$REGISTRY/catalog-refreshed-at"
cat > "$REGISTRY/README" <<'EOF'
Apache ecosystem package registry.
Only official ASF releases may be installed.
Each package records project, version, source URL, binary URL when applicable,
SHA-256, signature status, LICENSE and NOTICE status.
EOF
echo "[INFO] Apache project catalog refreshed."
echo "[INFO] Use apache-sync to resolve and install official releases."
