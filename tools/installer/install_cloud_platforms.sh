#!/usr/bin/env bash

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
