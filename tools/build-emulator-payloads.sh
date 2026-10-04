#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/build-emulator-payloads.sh

Usage:
  tools/build-emulator-payloads.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -eu
ROOT=${1:-build/emulators}; mkdir -p "$ROOT/src" "$ROOT/bin" "$ROOT/payloads"
if command -v git >/dev/null 2>&1; then
 git clone --depth 1 https://github.com/grumpycoders/pcsx-redux.git "$ROOT/src/pcsx-redux" 2>/dev/null || true
 git clone --depth 1 https://github.com/PCSX2/pcsx2.git "$ROOT/src/pcsx2" 2>/dev/null || true
 git clone --depth 1 https://github.com/RPCS3/rpcs3.git "$ROOT/src/rpcs3" 2>/dev/null || true
 git clone --depth 1 https://github.com/shadps4-emu/shadPS4.git "$ROOT/src/shadps4" 2>/dev/null || true
fi
echo "Open-source emulator sources staged under $ROOT/src."
