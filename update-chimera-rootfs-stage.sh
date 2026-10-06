#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${CHIMERA_ROOT:-/mnt/c/tmp/ChimeraIIOS}"
BUILD_SCRIPT="$ROOT/build-chimera-iso.sh"
BACKUP_DIR="$ROOT/.chimera-rootfs-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
log(){ printf '[CHIMERA-ROOTFS] %s\n' "$*"; }
die(){ printf '[CHIMERA-ROOTFS][ERROR] %s\n' "$*" >&2; exit 1; }
[[ -d "$ROOT" ]] || die "ChimeraIIOS root not found: $ROOT"
[[ -f "$BUILD_SCRIPT" ]] || die "Missing build script: $BUILD_SCRIPT"
mkdir -p "$BACKUP_DIR"
cp -a -- "$BUILD_SCRIPT" "$BACKUP_DIR/build-chimera-iso.sh.$STAMP.bak"
chmod 0755 "$BUILD_SCRIPT"
command -v python3 >/dev/null || die "python3 is required"
python3 - "$BUILD_SCRIPT" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(encoding='utf-8',errors='replace')
if 'CHIMERA_ROOTFS_EXPORT_V3' in s:
    print('[CHIMERA-ROOTFS] already patched'); raise SystemExit(0)
helper=r'''
# CHIMERA_ROOTFS_EXPORT_V3
chimera_export_docker_rootfs() {
    local image="${1:-${CHIMERA_DOCKER_IMAGE:-${DOCKER_IMAGE:-}}}"
    local dest="${2:-${CHIMERA_ROOTFS_DIR:-${ROOTFS_DIR:-${ROOTFS:-}}}}"
    local work="${CHIMERA_ROOTFS_WORK:-/tmp/chimera-rootfs-work}"
    local cid='' tarball='' avail required=0 stage
    [[ -n "$image" ]] || { log_error "Docker image is not set for rootfs export."; return 1; }
    [[ -n "$dest" ]] || { log_error "Rootfs destination is not set; use CHIMERA_ROOTFS_DIR."; return 1; }
    command -v docker >/dev/null || { log_error "Docker CLI not found."; return 1; }
    command -v tar >/dev/null || { log_error "tar not found."; return 1; }
    docker image inspect "$image" >/dev/null 2>&1 || { log_error "Docker image does not exist: $image"; return 1; }
    mkdir -p "$work" "$dest"; chmod 0700 "$work"
    [[ -w "$dest" ]] || { log_error "Rootfs destination is not writable: $dest"; return 1; }
    required="$(docker image inspect -f '{{.Size}}' "$image" 2>/dev/null || echo 0)"; [[ "$required" =~ ^[0-9]+$ ]] || required=0
    required=$((required + 1073741824))
    avail="$(df -Pk "$work" | awk 'NR==2 {print $4*1024}')"; [[ "$avail" =~ ^[0-9]+$ ]] || avail=0
    (( required == 0 || avail >= required )) || { log_error "Insufficient WSL /tmp space: need about $required bytes, have $avail."; return 1; }
    rm -rf -- "$work/export" "$work/rootfs"
    mkdir -p "$work/export" "$work/rootfs"
    while read -r old; do [[ -z "$old" ]] || docker rm -f "$old" >/dev/null 2>&1 || true; done < <(docker ps -aq --filter 'label=chimera.rootfs.export=true')
    cid="$(docker create --label chimera.rootfs.export=true "$image")" || { log_error "docker create failed: $image"; return 1; }
    tarball="$work/export/rootfs.tar"
    log_info "Exporting $image -> $tarball"
    if ! docker export "$cid" -o "$tarball"; then
        docker logs "$cid" 2>&1 || true; docker rm -f "$cid" >/dev/null 2>&1 || true
        log_error "docker export failed"; return 1
    fi
    docker rm -f "$cid" >/dev/null 2>&1 || true; cid=''
    [[ -s "$tarball" ]] || { log_error "Docker export archive is empty: $tarball"; return 1; }
    log_info "Extracting rootfs on Linux-native WSL storage"
    tar --numeric-owner --xattrs --xattrs-include='*' --acls --same-permissions -xf "$tarball" -C "$work/rootfs" || { log_error "tar extraction failed; archive retained at $tarball"; return 1; }
    [[ -d "$work/rootfs/etc" ]] || { log_error "Invalid exported rootfs: /etc missing"; return 1; }
    stage="${dest}.chimera-new.$$"; rm -rf -- "$stage"; mkdir -p "$stage"
    cp -a -- "$work/rootfs/." "$stage/"
    rm -rf -- "$dest"; mv -- "$stage" "$dest"
    [[ -d "$dest/etc" ]] || { log_error "Final rootfs validation failed"; return 1; }
    rm -rf -- "$work/export" "$work/rootfs"
    log_info "Rootfs export completed: $dest"
}
type log_info >/dev/null 2>&1 || log_info(){ printf '[INFO] %s\n' "$*"; }
type log_error >/dev/null 2>&1 || log_error(){ printf '[ERROR] %s\n' "$*" >&2; }
# CHIMERA_ROOTFS_DIAGNOSTICS_V1
chimera_rootfs_err_report(){ local rc=$?; printf '[ERROR] rootfs command failed (rc=%s): %s\n' "$rc" "$BASH_COMMAND" >&2; return "$rc"; }
'''
s=s.replace('set -Eeuo pipefail','set -Eeuo pipefail\n'+helper,1)
start=None
lines=s.splitlines(True)
for i,l in enumerate(lines):
    low=l.lower()
    if ('step 2' in low and 'rootfs' in low) or 'export docker rootfs' in low:
        start=i; break
if start is None:
    for i,l in enumerate(lines):
        if re.search(r'(stage_rootfs|rootfs_stage|export_rootfs)',l,re.I): start=i; break
if start is None: raise SystemExit('ROOTFS_STAGE_NOT_FOUND: refusing unsafe modification')
end=len(lines)
for i in range(start+1,len(lines)):
    if re.search(r'^\s*(step\s+[3-9]|stage\s+[3-9])\b',lines[i],re.I): end=i; break
section=''.join(lines[start:end])
m=re.search(r'docker\s+build[^\n]*?(?:-t|--tag)\s+([^\s\\]+)',s,re.I)
image=(m.group(1).strip("'\"") if m else '${CHIMERA_DOCKER_IMAGE:-${DOCKER_IMAGE:-}}')
dest=next((('${'+n+'}') for n in ('ROOTFS_DIR','ROOTFS','DOCKER_ROOTFS','ROOTFS_PATH') if re.search(r'\b'+n+r'\s*=',s)), '${CHIMERA_ROOTFS_DIR:-${ROOTFS_DIR:-${ROOTFS:-}}}')
call=f'\n    log_info "STEP 2: exporting Docker rootfs"\n    chimera_export_docker_rootfs "{image}" "{dest}"\n'
if re.search(r'docker\s+export',section,re.I):
    section2=re.sub(r'^[^\n]*docker\s+export[^\n]*$',call.rstrip(),section,count=1,flags=re.I|re.M)
    if section2==section: raise SystemExit('ROOTFS_EXPORT_COMMAND_NOT_REPLACED')
    section=section2
else: section += call
lines[start:end]=[section]
p.write_text(''.join(lines),encoding='utf-8')
print('[CHIMERA-ROOTFS] patched rootfs stage')
PY
bash -n "$BUILD_SCRIPT" || die "Patched build script has syntax errors"
grep -q CHIMERA_ROOTFS_EXPORT_V3 "$BUILD_SCRIPT" || die "rootfs helper missing"
grep -q chimera_export_docker_rootfs "$BUILD_SCRIPT" || die "rootfs call missing"
grep -q CHIMERA_ROOTFS_DIAGNOSTICS_V1 "$BUILD_SCRIPT" || die "diagnostics missing"
chmod 0755 "$BUILD_SCRIPT"
log "PASS: rootfs export repaired"
log "PASS: WSL-native /tmp extraction enabled"
log "PASS: stale export containers cleaned"
log "PASS: rootfs validated before replacement"
log "Backup: $BACKUP_DIR/build-chimera-iso.sh.$STAMP.bak"
log "Run: cd $ROOT && ./build-chimera-iso.sh"
