#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build/build-native-toolchain.sh

Usage:
  tools/build/build-native-toolchain.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
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
export CHIMERA_ASSEMBLER="${CHIMERA_ASSEMBLER:-gnu}"
EOF

echo "Native Chimera toolchain staging complete: ${PREFIX}"
