#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFIX="${CHIMERA_TOOLCHAIN_PREFIX:-${ROOT}/build/native-toolchain}"
export CHIMERA_TOOLCHAIN_PREFIX="${PREFIX}"
export CHIMERA_SKIP_PACKAGE_INSTALL=1

"${ROOT}/tools/toolchain/install-native-toolchain.sh"

cat > "${PREFIX}/toolchain.env" <<EOF
export CHIMERA_SDK_ROOT="${PREFIX}"
export PATH="${PREFIX}/bin:\$PATH"
export CHIMERA_NATIVE_COMPILER="${CHIMERA_NATIVE_COMPILER:-gcc}"
export CHIMERA_NATIVE_LINKER="${CHIMERA_NATIVE_LINKER:-bfd}"
EOF

echo "Native Chimera toolchain staging complete: ${PREFIX}"
