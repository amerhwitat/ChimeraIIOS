#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$ROOT/tools/service-manager.sh"
PROVIDERS="$ROOT/tools/commands/install-command-providers.sh"
CATALOG="$ROOT/services/linux/service-catalog.json"
if [[ ! -f "$CATALOG" ]]; then CATALOG="$ROOT/config/services/linux-service-catalog.json"; fi
bash -n "$SCRIPT"
bash -n "$PROVIDERS"
python3 -m json.tool "$CATALOG" >/dev/null
python3 - "$CATALOG" "$PROVIDERS" <<'PY'
import json, pathlib, sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
provider=pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
ids={s["id"] for s in data["services"]}
assert len(ids)==len(data["services"]), "duplicate service IDs"
for profile, services in data["profiles"].items():
    missing=set(services)-ids
    assert not missing, f"{profile} profile has unknown IDs: {sorted(missing)}"
by_id={s["id"]:s for s in data["services"]}
required={"openssh-server","nginx","apache2","vsftpd","tftpd-hpa"}
assert required <= ids, f"missing daemon service definitions: {sorted(required-ids)}"
for service_id in required:
    assert service_id in data["policy"]["never_enable_without_admin"], f"{service_id} must require explicit admin enablement"
for service_id in ("vsftpd","tftpd-hpa"):
    assert by_id[service_id].get("default_enabled") is False, f"{service_id} must remain disabled by default"
for profile in ("network","server"):
    assert {"vsftpd","tftpd-hpa"} <= set(data["profiles"][profile]), f"{profile} profile missing FTP/TFTP"
for package in required:
    assert package in provider, f"provider package not staged: {package}"
for service in data["services"]:
    assert service.get("package") and service.get("unit"), service["id"]
PY
CHIMERA_SERVICE_CATALOG="$CATALOG" bash "$SCRIPT" help >/dev/null
if CHIMERA_SERVICE_CATALOG="$CATALOG" bash "$SCRIPT" status definitely-not-a-service >/dev/null 2>&1; then
  echo "unknown service id was accepted" >&2; exit 1
fi
echo "Chimera service manager and network daemon tests passed"
