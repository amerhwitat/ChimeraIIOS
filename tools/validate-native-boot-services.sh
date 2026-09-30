#!/usr/bin/env bash
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
