#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/installer/install_openstack_tools.sh

Usage:
  tools/installer/install_openstack_tools.sh [options] [arguments]

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
# Install OpenStack CLI tooling on a Debian/Ubuntu-compatible Chimera II OS installation.
if [[ "${EUID}" -ne 0 ]]; then echo "Run as root (or through sudo)." >&2; exit 1; fi
command -v apt-get >/dev/null 2>&1 || { echo "This installer currently targets Debian/Ubuntu-compatible Chimera installations." >&2; exit 2; }
apt-get update
apt-get install -y python3 python3-pip python3-venv ca-certificates
python3 -m venv /opt/chimera-openstack-venv
/opt/chimera-openstack-venv/bin/pip install --upgrade pip openstackclient
ln -sf /opt/chimera-openstack-venv/bin/openstack /usr/local/bin/openstack
printf '%s\n' 'OpenStack client installed. Configure an external OpenStack cloud credential/application credential before use.'
