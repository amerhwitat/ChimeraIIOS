#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/dualboot/chimera-dualboot-macos.sh

Usage:
  tools/dualboot/chimera-dualboot-macos.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail
echo "Chimera II macOS dual-boot planner"
echo "Planner-only: does not modify APFS, SIP, Secure Boot, or Apple boot policy."
echo "For macOS use the hosted QEMU/HVF path for supported guest architectures."
uname -a
