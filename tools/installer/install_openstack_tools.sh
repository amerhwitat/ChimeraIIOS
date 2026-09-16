#!/usr/bin/env bash
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
