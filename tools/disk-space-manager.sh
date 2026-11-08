#!/usr/bin/env bash

# --- Chimera II OS standard help ---
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'CHIMERA_HELP'
Chimera II OS script: tools/disk-space-manager.sh

Usage:
  tools/disk-space-manager.sh [options] [arguments]

Options:
  -h, --help    Show this help and exit successfully.

Notes:
  This help entry is provided consistently across Chimera II OS shell tools.
  The script's existing command-line interface and environment variables remain unchanged.
CHIMERA_HELP
  exit 0
fi
set -euo pipefail

ROOT="${CHIMERA_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
fi
BUILD_ROOT="${CHIMERA_BUILD_DIR:-$ROOT/build}"
mkdir -p "$BUILD_ROOT"
REPORT="${CHIMERA_DISK_REPORT:-$BUILD_ROOT/reports/disk-space.json}"
MIN_FREE_GB="${CHIMERA_MIN_FREE_GB:-30}"
EXPECTED_GB="${CHIMERA_EXPECTED_BUILD_GB:-20}"
RESERVE_GB="${CHIMERA_DISK_RESERVE_GB:-0}"
AUTO_CLEAN="${CHIMERA_AUTO_CLEAN_DISK:-1}"
CLEAN_THRESHOLD_GB="${CHIMERA_CLEAN_THRESHOLD_GB:-6}"
MIN_REPO_FREE_GB="${CHIMERA_MIN_REPO_FREE_GB:-1}"

mkdir -p "$(dirname "$REPORT")"
log(){ printf '[DISK] %s\n' "$*" >&2; }
warn(){ printf '[DISK][WARN] %s\n' "$*" >&2; }
bytes_to_gb(){ awk -v b="$1" 'BEGIN { printf "%.2f", b/1073741824 }'; }
path_free_gb(){
  local p="$1" b
  b="$(df -Pk "$p" 2>/dev/null | awk 'NR==2 {print $4*1024}' || true)"
  [[ "$b" =~ ^[0-9]+$ ]] && bytes_to_gb "$b" || echo "0.00"
}
device_for(){
  df -P "$1" 2>/dev/null | awk 'NR==2 {print $1}' || true
}
min_gb(){
  awk -v a="$1" -v b="$2" 'BEGIN {printf "%.2f",(a<b?a:b)}'
}
recompute_capacity(){
  build_free_gb="$(path_free_gb "$BUILD_ROOT")"
  repo_free_gb="$(path_free_gb "$ROOT")"
  docker_free_gb="0.00"
  docker_root=""
  docker_ok=0
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    docker_ok=1
    docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
    [[ -d "$docker_root" ]] && docker_free_gb="$(path_free_gb "$docker_root")"
  fi
  wsl_detected=0
  wsl_free_gb="0.00"
  if grep -qiE '(microsoft|wsl)' /proc/version 2>/dev/null || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    wsl_detected=1
    wsl_free_gb="$(path_free_gb /)"
  fi
  build_device="$(device_for "$BUILD_ROOT")"
  repo_device="$(device_for "$ROOT")"
  wsl_device="$(device_for /)"
  host_free_gb="$build_free_gb"
  effective_free_gb="$build_free_gb"
  # The repository checkout and selected build volume can be different
  # filesystems (for example /mnt/c source + /mnt/e build). Only combine their
  # free-space budgets when they are actually the same filesystem.
  if [[ -n "$repo_device" && "$repo_device" == "$build_device" ]]; then
    effective_free_gb="$(min_gb "$effective_free_gb" "$repo_free_gb")"
  fi
  if [[ "$docker_ok" == "1" && "$docker_free_gb" != "0.00" ]]; then
    effective_free_gb="$(min_gb "$effective_free_gb" "$docker_free_gb")"
  fi
  if [[ "$wsl_detected" == "1" && -n "$wsl_device" && "$wsl_device" == "$build_device" ]]; then
    effective_free_gb="$(min_gb "$effective_free_gb" "$wsl_free_gb")"
  fi
}

recompute_capacity
if [[ "$AUTO_CLEAN" == "1" ]] && awk -v f="$effective_free_gb" -v t="$CLEAN_THRESHOLD_GB" 'BEGIN {exit !(f<t)}'; then
  if [[ "$docker_ok" == "1" ]]; then
    log "Low storage detected on the selected build volume; reclaiming Docker build cache and unused images."
    docker builder prune -af >/dev/null 2>&1 || warn "docker builder prune failed"
    docker image prune -af >/dev/null 2>&1 || warn "docker image prune failed"
    docker container prune -f >/dev/null 2>&1 || warn "docker container prune failed"
  fi
  recompute_capacity
fi

status="ok"
if awk -v f="$effective_free_gb" -v need="$MIN_FREE_GB" -v expected="$EXPECTED_GB" -v r="$RESERVE_GB" 'BEGIN {exit !(f<need || f<expected+r)}'; then
  status="insufficient"
fi
if awk -v f="$repo_free_gb" -v need="$MIN_REPO_FREE_GB" 'BEGIN {exit !(f<need)}'; then
  status="insufficient"
fi

python3 - "$REPORT" "$status" "$EXPECTED_GB" "$MIN_FREE_GB" "$RESERVE_GB" "$build_free_gb" "$repo_free_gb" "$docker_free_gb" "$wsl_free_gb" "$effective_free_gb" "$docker_ok" "$docker_root" "$wsl_detected" "$AUTO_CLEAN" "$BUILD_ROOT" "$build_device" "$repo_device" "$wsl_device" "$MIN_REPO_FREE_GB" <<'PY'
import json,sys
keys=("report","status","required_build_gb","minimum_build_free_gb","reserve_gb",
      "available_build_gb","available_repo_gb","available_docker_gb","available_wsl_gb",
      "effective_available_gb","docker_available","docker_root","wsl_detected",
      "auto_cleanup","build_root","build_device","repo_device","wsl_device","minimum_repo_free_gb")
out=dict(zip(keys,sys.argv[1:]))
for k in keys:
    if k.endswith("_gb"): out[k]=float(out[k])
for k in ("docker_available","wsl_detected","auto_cleanup"): out[k]=out[k]=="1"
with open(out.pop("report"),"w",encoding="utf-8") as f: json.dump(out,f,indent=2)
PY

log "Build volume free: $build_free_gb GiB ($BUILD_ROOT); repository free: $repo_free_gb GiB ($ROOT); Docker free: $docker_free_gb GiB; WSL free: $wsl_free_gb GiB; effective build volume: $effective_free_gb GiB."
log "Report: $REPORT"

if [[ "$status" != "ok" ]]; then
  warn "Insufficient storage for the Chimera II OS build or final repository artifact."
  warn "The selected build volume must meet MIN_FREE_GB and EXPECTED_BUILD_GB + reserve; the repository filesystem must retain MIN_REPO_FREE_GB."
  warn "Docker Desktop's managed WSL VHDX grows dynamically; the build never modifies Docker's managed VHDX directly."
  exit 2
fi
