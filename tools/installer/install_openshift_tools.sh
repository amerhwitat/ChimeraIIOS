#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/installer/install_openshift_tools.sh

Usage:
  tools/installer/install_openshift_tools.sh [options] [arguments]

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
# Install OpenShift/OKD administration tooling. Cluster installation remains provider-specific.

if [[ "${EUID}" -ne 0 ]]; then echo "Run as root (or through sudo)." >&2; exit 1; fi
command -v apt-get >/dev/null 2>&1 || { echo "This installer currently targets Debian/Ubuntu-compatible Chimera installations." >&2; exit 2; }
apt-get update
apt-get install -y ca-certificates curl tar
printf '%s\n' 'OpenShift tooling requires a selected OKD/OpenShift release and matching oc/openshift-install binaries.'
printf '%s\n' 'Use the official release artifacts for the target platform; this script deliberately does not guess or silently download a release.'
printf '%s\n' 'After installation, verify with: oc version and openshift-install version'
