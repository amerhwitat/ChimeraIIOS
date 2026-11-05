#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

CATALOG="${CHIMERA_SERVICE_CATALOG:-/usr/share/chimera/service-catalog.json}"
ACTION="${1:-help}"
TARGET="${2:-}"

log(){ printf '[Chimera services] %s\n' "$*" >&2; }
die(){ log "ERROR: $*"; exit 1; }
need_catalog(){
  command -v python3 >/dev/null 2>&1 || die "python3 is required"
  [[ -r "$CATALOG" ]] || die "catalog not found: $CATALOG"
}
need_systemd(){
  command -v systemctl >/dev/null 2>&1 || die "systemctl is unavailable; this backend requires systemd"
}
need_root(){
  [[ "$EUID" -eq 0 ]] || die "run this action with sudo/root"
}
entry(){
  python3 - "$CATALOG" "$1" <<'PY'
import json,sys
with open(sys.argv[1],encoding="utf-8") as f:
    data=json.load(f)
for service in data.get("services",[]):
    if service.get("id")==sys.argv[2]:
        print("\t".join(str(service.get(k,"")) for k in ("id","package","unit","class","label")))
        raise SystemExit(0)
raise SystemExit(3)
PY
}
status_one(){
  local row id pkg unit cls label state enabled
  row="$(entry "$1")" || die "unknown service id: $1"
  IFS=$'\t' read -r id pkg unit cls label <<<"$row"
  state="$(systemctl is-active "$unit" 2>/dev/null || true)"
  enabled="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  printf '%-24s %-12s %-12s %s\n' "$id" "${state:-unknown}" "${enabled:-unknown}" "$label"
}
install_one(){
  local row id pkg unit cls label before_enabled before_active after_enabled after_active policy backup_policy=""
  row="$(entry "$1")" || die "unknown service id: $1"
  IFS=$'\t' read -r id pkg unit cls label <<<"$row"
  [[ -n "$pkg" ]] || die "no package mapping for $id"
  need_systemd
  before_enabled="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  before_active="$(systemctl is-active "$unit" 2>/dev/null || true)"
  policy="/usr/sbin/policy-rc.d"
  if [[ -e "$policy" ]]; then
    backup_policy="$(mktemp)"
    cp -a "$policy" "$backup_policy"
  fi
  restore_policy(){
    if [[ -n "$backup_policy" ]]; then
      cp -a "$backup_policy" "$policy"
      rm -f "$backup_policy"
    else
      rm -f "$policy"
    fi
  }
  printf '#!/bin/sh\nexit 101\n' >"$policy"
  chmod 0755 "$policy"
  trap restore_policy EXIT
  log "Installing package $pkg for $id without starting package-managed daemons"
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$pkg"
  restore_policy
  trap - EXIT
  after_enabled="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  after_active="$(systemctl is-active "$unit" 2>/dev/null || true)"
  if [[ "$before_enabled" != "enabled" && "$before_enabled" != "enabled-runtime" && "$after_enabled" == "enabled" ]]; then
    systemctl disable "$unit" || true
  fi
  if [[ "$before_active" != "active" && "$after_active" == "active" ]]; then
    systemctl stop "$unit" || true
  fi
}
unit_action(){
  local action="$1" row id pkg unit cls label
  row="$(entry "$2")" || die "unknown service id: $2"
  IFS=$'\t' read -r id pkg unit cls label <<<"$row"
  if [[ "$cls" == "core" && "$action" =~ ^(disable|stop|restart|disable-now)$ ]]; then
    die "refusing to $action protected core service $id"
  fi
  case "$action" in
    enable) systemctl enable "$unit" ;;
    disable) systemctl disable "$unit" ;;
    start) systemctl start "$unit" ;;
    stop) systemctl stop "$unit" ;;
    restart) systemctl restart "$unit" ;;
    enable-now) systemctl enable --now "$unit" ;;
    disable-now) systemctl disable --now "$unit" ;;
    *) die "unsupported service action: $action" ;;
  esac
}
profile_install(){
  local profile="$1" id
  mapfile -t services < <(python3 - "$CATALOG" "$profile" <<'PY'
import json,sys
with open(sys.argv[1],encoding="utf-8") as f:
    data=json.load(f)
profile=data.get("profiles",{}).get(sys.argv[2])
if profile is None:
    raise SystemExit("unknown profile: "+sys.argv[2])
for service_id in profile:
    print(service_id.strip())
PY
)
  for id in "${services[@]}"; do
    [[ -n "$id" ]] || continue
    install_one "$id"
  done
}
usage(){
  cat <<'EOF'
Chimera Linux Service Manager
Usage:
  chimera-services list
  chimera-services status [service-id]
  chimera-services install <service-id>
  chimera-services profile <base|desktop|network|server|storage|security|developer>
  chimera-services enable|disable|start|stop|restart|enable-now|disable-now <service-id>
  chimera-services help
Install/profile/enable/disable/start/stop/restart operations require root.
Services are installed on demand. Network listeners are never enabled by profile install.
EOF
}

need_catalog
case "$ACTION" in
  help|-h|--help) usage ;;
  list)
    need_systemd
    printf '%-24s %-12s %-12s %s\n' ID ACTIVE ENABLED DESCRIPTION
    while IFS= read -r id; do
      [[ -n "$id" ]] && status_one "$id"
    done < <(python3 - "$CATALOG" <<'PY'
import json,sys
with open(sys.argv[1],encoding="utf-8") as f:
    for service in json.load(f).get("services",[]):
        print(service["id"])
PY
)
    ;;
  status)
    if [[ -n "$TARGET" ]]; then need_systemd; status_one "$TARGET"; else "$0" list; fi
    ;;
  install)
    [[ -n "$TARGET" ]] || die "service id required"
    need_root; need_systemd; install_one "$TARGET"
    ;;
  profile)
    [[ -n "$TARGET" ]] || die "profile name required"
    need_root; need_systemd; profile_install "$TARGET"
    ;;
  enable|disable|start|stop|restart|enable-now|disable-now)
    [[ -n "$TARGET" ]] || die "service id required"
    need_root; need_systemd; unit_action "$ACTION" "$TARGET"
    ;;
  *) usage; die "unknown action: $ACTION" ;;
esac
