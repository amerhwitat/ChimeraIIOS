#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then echo "initialize-accounts: run as root" >&2; exit 77; fi
ROOT=${CHIMERA_SYSROOT:-}
export CHIMERA_SYSROOT="$ROOT"
chm-user-setup init
if [ "${CHIMERA_CREATE_ROOT:-1}" = 1 ]; then chm-user-setup create-root; fi
echo "Chimera local account database initialized."
