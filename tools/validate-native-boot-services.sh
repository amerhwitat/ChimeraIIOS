#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/validate-native-boot-services.sh

Usage:
  tools/validate-native-boot-services.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 tools/tests/test_service_registry.py
python3 tools/tests/test_installer_service_selection.py
python3 tools/tests/test_boot_modes.py
python3 tools/tests/test_boot_measurements.py
python3 tools/tests/test_hardware_profile.py
python3 tools/chimera_service_plan.py minimal-desktop >/dev/null
python3 tools/chimera_service_plan.py enterprise-server >/dev/null
bash -n kernel/build-koronos.sh
bash -n tools/validate-native-boot-services.sh
printf 'PASS: native boot/service contract validation completed\n'
