#!/bin/sh

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: hardware/host-agents/macos/scan-hardware.sh

Usage:
  hardware/host-agents/macos/scan-hardware.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi

# Resolve the repository root from this script location; never depend on the caller's working directory.
CHIMERA_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$CHIMERA_REPO_ROOT"
set -eu
python3 - <<'PY'
import json,subprocess,platform,datetime
def r(c):
 try:return subprocess.check_output(c,text=True,stderr=subprocess.STDOUT,timeout=30)
 except Exception:return ""
print(json.dumps({"schema":"chimera-hardware-inventory-v1","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"host":{"os":"Darwin","release":platform.release(),"machine":platform.machine()},"devices":[{"class":"system_profiler","raw":r(["system_profiler","SPHardwareDataType","SPPCIDataType","SPUSBDataType","SPDisplaysDataType","SPNetworkDataType"])},{"class":"ioreg","raw":r(["ioreg","-l"])}]},indent=2))
PY
