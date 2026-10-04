#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/installer/install_cloud_platforms.sh

Usage:
  tools/installer/install_cloud_platforms.sh [options] [arguments]

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
usage() { echo "Usage: $0 [kubernetes|openshift|openstack|all]"; }
TARGET="${1:-all}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
case "$TARGET" in
  kubernetes) "$ROOT/tools/installer/install_kubernetes.sh" ;;
  openshift) "$ROOT/tools/installer/install_openshift_tools.sh" ;;
  openstack) "$ROOT/tools/installer/install_openstack_tools.sh" ;;
  all)
    "$ROOT/tools/installer/install_kubernetes.sh"
    "$ROOT/tools/installer/install_openshift_tools.sh"
    "$ROOT/tools/installer/install_openstack_tools.sh"
    ;;
  *) usage; exit 2 ;;
esac
