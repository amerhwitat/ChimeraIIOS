#!/usr/bin/env bash
set -euo pipefail
ROOT="$CHIMERA_ROOT"
if [[ -z "$ROOT" ]]; then ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"; fi
REPORT="$CHIMERA_DISK_REPORT"
[[ -n "$REPORT" ]] || REPORT="$ROOT/build/reports/disk-space.json"
MIN_FREE_GB="$CHIMERA_MIN_FREE_GB"; [[ -n "$MIN_FREE_GB" ]] || MIN_FREE_GB=100
EXPECTED_GB="$CHIMERA_EXPECTED_BUILD_GB"; [[ -n "$EXPECTED_GB" ]] || EXPECTED_GB=80
RESERVE_GB="$CHIMERA_DISK_RESERVE_GB"; [[ -n "$RESERVE_GB" ]] || RESERVE_GB=20
AUTO_CLEAN="$CHIMERA_AUTO_CLEAN_DISK"; [[ -n "$AUTO_CLEAN" ]] || AUTO_CLEAN=1
CLEAN_THRESHOLD_GB="$CHIMERA_CLEAN_THRESHOLD_GB"
[[ -n "$CLEAN_THRESHOLD_GB" ]] || CLEAN_THRESHOLD_GB=$((MIN_FREE_GB + RESERVE_GB))

mkdir -p "$(dirname "$REPORT")"
log(){ printf '[DISK] %s\n' "$*" >&2; }
warn(){ printf '[DISK][WARN] %s\n' "$*" >&2; }
bytes_to_gb(){ awk -v b="$1" 'BEGIN { printf "%.2f", b/1073741824 }'; }
path_free_gb(){
  local p="$1" b
  b="$(df -Pk "$p" 2>/dev/null | awk 'NR==2 {print $4*1024}' || true)"
  [[ "$b" =~ ^[0-9]+$ ]] && bytes_to_gb "$b" || echo "0.00"
}

docker_ok=0
docker_free_gb="0.00"
docker_root=""
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker_ok=1
  docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
  [[ -d "$docker_root" ]] && docker_free_gb="$(path_free_gb "$docker_root")"
fi

wsl_detected=0
wsl_free_gb="0.00"
if grep -qiE '(microsoft|wsl)' /proc/version 2>/dev/null || [[ -n "$WSL_DISTRO_NAME" ]]; then
  wsl_detected=1
  wsl_free_gb="$(path_free_gb /)"
fi

host_free_gb="$(path_free_gb "$ROOT")"
effective_free_gb="$host_free_gb"
for candidate in "$docker_free_gb" "$wsl_free_gb"; do
  if awk -v x="$candidate" 'BEGIN {exit !(x>0)}'; then
    effective_free_gb="$(awk -v a="$effective_free_gb" -v b="$candidate" 'BEGIN {printf "%.2f",(a<b?a:b)}')"
  fi
done

cleanup_docker(){
  [[ "$docker_ok" == "1" ]] || return 0
  log "Low storage detected; reclaiming Docker build cache and unused images."
  docker builder prune -af >/dev/null 2>&1 || warn "docker builder prune failed"
  docker image prune -af >/dev/null 2>&1 || warn "docker image prune failed"
  docker container prune -f >/dev/null 2>&1 || warn "docker container prune failed"
}

if [[ "$AUTO_CLEAN" == "1" ]] && awk -v f="$effective_free_gb" -v t="$CLEAN_THRESHOLD_GB" 'BEGIN {exit !(f<t)}'; then
  cleanup_docker
  host_free_gb="$(path_free_gb "$ROOT")"
  [[ "$docker_ok" == "1" && -d "$docker_root" ]] && docker_free_gb="$(path_free_gb "$docker_root")"
  effective_free_gb="$host_free_gb"
  for candidate in "$docker_free_gb" "$wsl_free_gb"; do
    if awk -v x="$candidate" 'BEGIN {exit !(x>0)}'; then
      effective_free_gb="$(awk -v a="$effective_free_gb" -v b="$candidate" 'BEGIN {printf "%.2f",(a<b?a:b)}')"
    fi
  done
fi

status="ok"
if awk -v f="$effective_free_gb" -v need="$MIN_FREE_GB" -v exp="$EXPECTED_GB" -v r="$RESERVE_GB" 'BEGIN {exit !(f<need || f<exp+r)}'; then
  status="insufficient"
fi

python3 - "$REPORT" "$status" "$EXPECTED_GB" "$MIN_FREE_GB" "$RESERVE_GB" "$host_free_gb" "$docker_free_gb" "$wsl_free_gb" "$effective_free_gb" "$docker_ok" "$docker_root" "$wsl_detected" "$AUTO_CLEAN" <<'PY'
import json,sys
keys=("report","status","required_build_gb","minimum_free_gb","reserve_gb","available_host_gb","available_docker_gb","available_wsl_gb","effective_available_gb","docker_available","docker_root","wsl_detected","auto_cleanup")
out=dict(zip(keys,sys.argv[1:]))
for k in keys:
    if k.endswith("_gb"): out[k]=float(out[k])
for k in ("docker_available","wsl_detected","auto_cleanup"): out[k]=out[k]=="1"
with open(out.pop("report"),"w") as f: json.dump(out,f,indent=2)
PY

log "Host free: $host_free_gb GiB; Docker free: $docker_free_gb GiB; WSL free: $wsl_free_gb GiB; effective: $effective_free_gb GiB."
log "Report: $REPORT"

if [[ "$status" != "ok" ]]; then
  warn "Insufficient storage for the Chimera II OS build."
  warn "Docker Desktop's managed WSL VHDX grows dynamically up to its configured storage limit and available host space."
  warn "Increase Docker Desktop's disk usage limit through Docker Desktop settings if required."
  warn "The build never modifies Docker's managed VHDX directly."
  exit 2
fi
