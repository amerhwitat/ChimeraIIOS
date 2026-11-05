#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/tools/service-manager.sh"
CATALOG="$ROOT/services/linux/service-catalog.json"
bash -n "$SCRIPT"
python3 -m json.tool "$CATALOG" >/dev/null
python3 - "$CATALOG" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
ids={s["id"] for s in data["services"]}
assert len(ids)==len(data["services"]), "duplicate service IDs"
for profile, services in data["profiles"].items():
    missing=set(services)-ids
    assert not missing, f"{profile} profile has unknown IDs: {sorted(missing)}"
for service in data["services"]:
    assert service.get("package") and service.get("unit"), service["id"]
PY
CHIMERA_SERVICE_CATALOG="$CATALOG" bash "$SCRIPT" help >/dev/null
if CHIMERA_SERVICE_CATALOG="$CATALOG" bash "$SCRIPT" status definitely-not-a-service >/dev/null 2>&1; then
  echo "unknown service id was accepted" >&2; exit 1
fi
echo "Chimera service manager static tests passed"
